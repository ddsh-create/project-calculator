from drafter import *
from dataclasses import dataclass
from bakery import assert_equal

# --- 1. Dataclasses ---

@dataclass
class Part:
    name: str 
    material: str 
    weight: float 
    cost: float 
    quantity: int
    subsystem: str = "Other"
    status: str = "Not Purchased" 
    vendor: str = ""
    url: str = ""
    notes: str = ""

@dataclass
class Project:
    name: str
    parts: list[Part]
    budget: float
    max_weight: float
    current_filter: str
    current_sort: str
    current_search: str
    status_message: str
    editing_part_name: str = ""
    show_purchased: bool = True

@dataclass
class State:
    projects: list[Project]
    current_project_name: str
    global_message: str
    total_projects_created: int 

# --- Helper Function ---
def get_current_project(state: State) -> Project:
    """
    Retrieves the currently active project from the application state based on the current_project_name.
    Returns the Project object if found, otherwise returns None.
    """
    for p in state.projects:
        if p.name == state.current_project_name:
            return p
    return None

# --- 2. Routes & Pages ---

@route
def index(state: State) -> Page:
    """
    Renders the main Projects Hub page where users can view all existing projects, 
    open a specific project, delete projects, or create a new project.
    """
    content = [
        Header("📂 Projects Hub"),
        Div([Text(f"Total Projects Created Lifetime: {state.total_projects_created}")]),
        Text(""),
    ]
    
    if state.global_message:
        content.extend([Div([Text(f"⚠️ {state.global_message}")]), Text("")])
    
    if len(state.projects) > 0:
        project_names = [p.name for p in state.projects]
        default_selection = state.current_project_name if state.current_project_name in project_names else project_names[0]
            
        content.extend([
            Div([Text("MANAGE PROJECTS:")]),
            Div([
                SelectBox("selected_project", project_names, default_selection),
                Button("Open Project", open_project_action),
                Button("Delete Project", delete_project_action)
            ]),
            Text(""), Text("")
        ])
    else:
        content.extend([Div([Text("No projects yet. Create one below!")]), Text("")])
        
    content.extend([
        Div([Text("CREATE A NEW PROJECT:")]),
        Div([
            TextBox("new_project_name", ""),
            Button("Create Project", create_project_action)
        ]),
        Text(""), Text(""),
        Div([Button("ℹ️ About This Tool", about_route)])
    ])
    
    return Page(state, content)

@route
def create_project_action(state: State, new_project_name: str) -> Page:
    """
    Validates and creates a new project with default settings, adds it to the state's 
    project list, updates the current active project, and navigates to the new project's dashboard.
    """
    if new_project_name == "" or new_project_name.isspace():
        state.global_message = "Project name cannot be empty."
        return index(state)
        
    for p in state.projects:
        if p.name == new_project_name:
            state.global_message = f"Project '{new_project_name}' already exists."
            return index(state)
            
    new_project = Project(new_project_name, [], 1000.0, 50.0, "All", "Name (A-Z)", "", "", "", True)
    state.projects.append(new_project)
    state.current_project_name = new_project_name
    state.global_message = ""
    state.total_projects_created += 1
    return project_dashboard(state)

@route
def open_project_action(state: State, selected_project: str) -> Page:
    """
    Updates the state's active project name to the user's selection and routes them 
    to that project's dashboard.
    """
    state.current_project_name = selected_project
    state.global_message = ""
    return project_dashboard(state)

@route
def delete_project_action(state: State, selected_project: str) -> Page:
    """
    Removes the specified project from the state's list of projects and 
    clears the active project selection if the currently opened project was deleted.
    """
    state.projects = [p for p in state.projects if p.name != selected_project]
    state.global_message = f"Project '{selected_project}' was deleted."
    if state.current_project_name == selected_project:
        state.current_project_name = ""
    return index(state)

@route
def project_dashboard(state: State) -> Page:
    """
    Renders the overview dashboard for the currently active project, displaying 
    aggregate metrics (total parts, weight, cost) and quick action navigation links.
    """
    project = get_current_project(state)
    if not project: return index(state)
        
    total_parts = sum(part.quantity for part in project.parts)
    total_weight = sum(part.weight * part.quantity for part in project.parts)
    total_cost = sum(part.cost * part.quantity for part in project.parts)
        
    content = [
        Header(f"📊 Dashboard: {project.name}"),
        Text("")
    ]

    if project.status_message:
        content.extend([Div([Text(f"🔔 {project.status_message}")]), Text("")])

    content.extend([
        Div([Text("PROJECT METRICS:")]),
        Div([Text(f"  • Total Individual Parts: {total_parts}")]),
        Div([Text(f"  • Combined Weight: {total_weight} lbs / {project.max_weight} lbs")]),
        Div([Text(f"  • Current Budget Spent: ${total_cost} / ${project.budget}")]),
        Text(""), Text(""),
        
        Div([Text("QUICK ACTIONS:")]),
        Div([
            Button("📋 View Inventory", inventory_route),
            Button("➕ Add New Part", add_part_form_route),
            Button("💰 Calculator & Limits", calculator_route)
        ]),
        Text(""), Text(""),
        Div([Button("🔙 Back to Projects Hub", index)])
    ])
    return Page(state, content)

@route
def inventory_route(state: State) -> Page:
    """
    Displays the project's entire parts inventory. Applies current search, sorting, 
    and filtering preferences. Allows users to change part statuses and manage individual parts.
    """
    project = get_current_project(state)
    purchased_statuses = ["Ordered", "Received"]
    total_spent = sum(p.cost * p.quantity for p in project.parts if p.status in purchased_statuses)
    total_projected = sum(p.cost * p.quantity for p in project.parts)
    
    content = [
        Header(f"📋 Inventory: {project.name}"),
        Div([
            Button("🔙 Back to Dashboard", project_dashboard)
        ]),
        Text("")
    ]

    if total_projected > project.budget:
        content.extend([Div([Text("🔴 🚨 WARNING: PROJECT BUDGET EXCEEDED! 🚨 🔴")]), Text("")])

    if project.status_message:
        content.extend([Div([Text(f"🔔 {project.status_message}")]), Text("")])

    content.extend([
        Div([Text("FINANCIAL OVERVIEW:")]),
        Div([Text(f"  • Spent (Ordered/Received): ${total_spent}")]),
        Div([Text(f"  • Projected (All): ${total_projected}")]),
        Div([Text(f"  • Total Budget: ${project.budget}")]),
        Text(""), Text("")
    ])

    visible_parts = [p for p in project.parts]
    if project.current_search:
        visible_parts = [p for p in visible_parts if project.current_search.lower() in p.name.lower()]

    if not project.show_purchased:
        visible_parts = [p for p in visible_parts if p.status not in purchased_statuses]
        
    if project.current_sort == "Cost (High to Low)":
        visible_parts.sort(key=lambda p: p.cost * p.quantity, reverse=True)
    elif project.current_sort == "Cost (Low to High)":
        visible_parts.sort(key=lambda p: p.cost * p.quantity)
    elif project.current_sort == "Material":
        visible_parts.sort(key=lambda p: p.material)
    elif project.current_sort == "Subsystem":
        visible_parts.sort(key=lambda p: p.subsystem)
    else: 
        visible_parts.sort(key=lambda p: p.name)

    content.extend([
        Div([Text("VIEW OPTIONS:")]),
        Div([
            Text("Search: "), TextBox("search_query", project.current_search),
            Text("  |  Sort: "), SelectBox("sort_by", ["Name (A-Z)", "Cost (High to Low)", "Cost (Low to High)", "Material", "Subsystem"], project.current_sort)
        ]),
        Div([
            CheckBox("show_purchased", project.show_purchased),
            Text(" Show Ordered/Received Items  "),
            Button("Apply View", update_inventory_view_action)
        ]),
        Text(""), Text("")
    ])

    content.append(Div([Text("PARTS LIST:")]))
    if not visible_parts:
        content.extend([Div([Text("  No parts match the current view.")]), Text("")])
    else:
        status_options = ["Not Purchased", "Ordered", "Received", "Needs Reorder"]
        status_icons = {"Not Purchased": "❌", "Ordered": "🚚", "Received": "✅", "Needs Reorder": "🔄"}
        
        for p in visible_parts:
            icon = status_icons.get(p.status, "📦")
            content.extend([
                Div([Text(f"📦 {p.name.upper()} ({p.material} - {p.subsystem}) — {p.quantity} units")]),
                Div([
                    Text(f"      Cost: ${p.cost * p.quantity} | Weight: {p.weight * p.quantity} lbs | {icon} Status: "), 
                    SelectBox(f"status_{p.name}", status_options, p.status)
                ])
            ])
            if p.vendor or p.url:
                v_str = p.vendor if p.vendor else "N/A"
                u_str = f" | Link: {p.url}" if p.url else ""
                content.append(Div([Text(f"      🛒 Vendor: {v_str}{u_str}")]))
            if p.notes:
                content.append(Div([Text(f"      📝 Notes: {p.notes}")]))
                
            content.append(Text(""))
        
        content.extend([
            Div([Button("💾 Save Statuses", save_statuses_action)]),
            Text("")
        ])

    if project.parts:
        part_names = [p.name for p in project.parts]
        content.extend([
            Text(""),
            Div([Text("⚙️ MANAGE INVENTORY:")]),
            Div([
                Text("Edit, Duplicate, or Remove a Part: "),
                SelectBox("selected_part_name", part_names, part_names[0])
            ]),
            Div([
                Button("Edit Part", edit_part_setup_action),
                Button("Duplicate Part", duplicate_part_action),
                Button("Remove Part", remove_part_action) 
            ])
        ])

    return Page(state, content)

@route
def save_statuses_action(state: State, **kwargs) -> Page:
    """
    Parses dynamic kwargs corresponding to part status select boxes in the inventory 
    and updates the purchase status of each part accordingly.
    """
    project = get_current_project(state)
    updated_count = 0
    
    for key, value in kwargs.items():
        if key.startswith("status_"):
            part_name = key.replace("status_", "", 1)
            for p in project.parts:
                if p.name == part_name:
                    if p.status != str(value):
                        p.status = str(value)
                        updated_count += 1
                    break
                    
    project.status_message = f"Updated status for {updated_count} part(s)."
    return inventory_route(state)

@route
def update_inventory_view_action(state: State, search_query: str, sort_by: str, show_purchased: bool) -> Page:
    """
    Updates the active project's search, sorting, and filtering state variables based 
    on the user's view preferences on the inventory page.
    """
    project = get_current_project(state)
    project.current_search = search_query
    project.current_sort = sort_by
    project.show_purchased = show_purchased
    project.status_message = "View preferences updated."
    return inventory_route(state)

@route
def duplicate_part_action(state: State, selected_part_name: str) -> Page:
    """
    Finds the selected part in the active project and creates an exact copy of it 
    appended with ' (Copy)' in its name, adding it to the inventory.
    """
    project = get_current_project(state)
    part_to_copy = next((p for p in project.parts if p.name == selected_part_name), None)
    if part_to_copy:
        new_part = Part(
            name=part_to_copy.name + " (Copy)",
            material=part_to_copy.material,
            weight=part_to_copy.weight,
            cost=part_to_copy.cost,
            quantity=part_to_copy.quantity,
            subsystem=part_to_copy.subsystem,
            status="Not Purchased",
            vendor=part_to_copy.vendor,
            url=part_to_copy.url,
            notes=part_to_copy.notes
        )
        project.parts.append(new_part)
        project.status_message = f"Successfully duplicated '{selected_part_name}'."
    return inventory_route(state)

@route
def remove_part_action(state: State, selected_part_name: str) -> Page:
    """
    Deletes the selected part from the active project's inventory.
    """
    project = get_current_project(state)
    project.parts = [p for p in project.parts if p.name != selected_part_name]
    project.status_message = f"'{selected_part_name}' was successfully removed."
    return inventory_route(state)

@route
def edit_part_setup_action(state: State, selected_part_name: str) -> Page:
    """
    Sets the active project's 'editing_part_name' state to match the user's selection 
    and redirects them to the dedicated edit part page.
    """
    project = get_current_project(state)
    project.editing_part_name = selected_part_name
    project.status_message = ""
    return edit_part_page(state)

@route
def edit_part_page(state: State) -> Page:
    """
    Renders the form page prepopulated with a specific part's data, allowing the user 
    to modify the part's characteristics, metrics, and sourcing notes.
    """
    project = get_current_project(state)
    part_to_edit = next((p for p in project.parts if p.name == project.editing_part_name), None)
            
    if not part_to_edit:
        project.status_message = "Error: Could not find the selected part."
        return inventory_route(state)

    return Page(
        state,
        [
            Header(f"✏️ Edit Part: {part_to_edit.name}"),
            Div([Text(f"🔔 {project.status_message}")] if project.status_message else Text("")),
            Text(""),
            Div([Text("PART DETAILS:")]),
            Div([Text("Name: "), TextBox("part_name", part_to_edit.name)]),
            Div([Text("Subsystem: "), SelectBox("part_subsystem", ["Mechanical", "Electrical", "Hardware", "Aesthetics", "Other"], part_to_edit.subsystem)]),
            Div([Text("Material: "), SelectBox("part_material", ["Aluminum", "Steel", "Brass", "Wood", "Other"], part_to_edit.material)]),
            Text(""),
            Div([Text("METRICS (Per Item):")]),
            Div([Text("Quantity: "), TextBox("part_quantity", str(part_to_edit.quantity))]),
            Div([Text("Weight (lbs): "), TextBox("part_weight", str(part_to_edit.weight))]),
            Div([Text("Cost ($): "), TextBox("part_cost", str(part_to_edit.cost))]),
            Text(""),
            Div([Text("SOURCING & NOTES (Optional):")]),
            Div([Text("Vendor: "), TextBox("part_vendor", part_to_edit.vendor)]),
            Div([Text("URL: "), TextBox("part_url", part_to_edit.url)]),
            Div([Text("Notes / Tolerances: "), TextBox("part_notes", part_to_edit.notes)]),
            Text(""), Text(""),
            Div([
                Button("Save Changes", update_part_action),
                Button("Cancel", inventory_route)
            ])
        ]
    )

@route
def update_part_action(state: State, part_name: str, part_subsystem: str, part_quantity: str, part_weight: str, part_cost: str, part_material: str, part_vendor: str, part_url: str, part_notes: str) -> Page:
    """
    Validates form submissions from the edit part page and updates the data of 
    the currently targeted part. Redirects back to inventory upon success.
    """
    project = get_current_project(state)
    if not part_name or part_name.isspace():
        project.status_message = "Error: Part name cannot be empty."
        return edit_part_page(state)
    
    try:
        weight_val, cost_val, quantity_val = float(part_weight), float(part_cost), int(part_quantity)
    except ValueError:
        project.status_message = "Error: Invalid number entries."
        return edit_part_page(state)

    if weight_val < 0 or cost_val < 0 or quantity_val < 1:
        project.status_message = "Error: Values cannot be negative, and quantity must be at least 1."
        return edit_part_page(state)

    for p in project.parts:
        if p.name == project.editing_part_name:
            p.name, p.subsystem, p.material = part_name, part_subsystem, part_material
            p.weight, p.cost, p.quantity = weight_val, cost_val, quantity_val
            p.vendor, p.url, p.notes = part_vendor.strip(), part_url.strip(), part_notes.strip()
            break
            
    project.status_message = f"'{part_name}' has been updated."
    project.editing_part_name = "" 
    return inventory_route(state)

@route
def add_part_form_route(state: State) -> Page:
    """
    Renders an empty form page allowing a user to input data and metrics to 
    create a brand new part for the active project.
    """
    project = get_current_project(state)
    return Page(
        state,
        [
            Header(f"➕ Add Component to {project.name}"),
            Div([Text(f"🔔 {project.status_message}")] if project.status_message else Text("")),
            Text(""),
            Div([Text("PART DETAILS:")]),
            Div([Text("Name: "), TextBox("part_name", "")]),
            Div([Text("Subsystem: "), SelectBox("part_subsystem", ["Mechanical", "Electrical", "Hardware", "Aesthetics", "Other"], "Mechanical")]),
            Div([Text("Material: "), SelectBox("part_material", ["Aluminum", "Steel", "Brass", "Wood", "Other"], "Aluminum")]),
            Text(""),
            Div([Text("METRICS (Per Item):")]),
            Div([Text("Quantity: "), TextBox("part_quantity", "")]),
            Div([Text("Weight (lbs): "), TextBox("part_weight", "")]),
            Div([Text("Cost ($): "), TextBox("part_cost", "")]),
            Text(""),
            Div([Text("SOURCING & NOTES (Optional):")]),
            Div([Text("Vendor: "), TextBox("part_vendor", "")]),
            Div([Text("URL: "), TextBox("part_url", "")]),
            Div([Text("Notes / Tolerances: "), TextBox("part_notes", "")]),
            Text(""), Text(""),
            Div([
                Button("Save Part", add_part_action),
                Button("Cancel", project_dashboard)
            ])
        ]
    )

@route
def add_part_action(state: State, part_name: str, part_subsystem: str, part_quantity: str, part_weight: str, part_cost: str, part_material: str, part_vendor: str, part_url: str, part_notes: str) -> Page:
    """
    Validates form submissions from the add part page, creates a new Part object, 
    and appends it to the active project's parts list.
    """
    project = get_current_project(state)
    if not part_name or part_name.isspace():
        project.status_message = "Error: Part name cannot be empty."
        return add_part_form_route(state)
    try:
        weight_val, cost_val, quantity_val = float(part_weight), float(part_cost), int(part_quantity)
    except ValueError:
        project.status_message = "Error: Number error in form inputs."
        return add_part_form_route(state)

    if weight_val < 0 or cost_val < 0 or quantity_val < 1:
        project.status_message = "Error: Values cannot be negative, and quantity must be at least 1."
        return add_part_form_route(state)

    project.parts.append(Part(
        name=part_name, 
        material=part_material, 
        weight=weight_val, 
        cost=cost_val, 
        quantity=quantity_val, 
        subsystem=part_subsystem, 
        status="Not Purchased",
        vendor=part_vendor.strip(),
        url=part_url.strip(),
        notes=part_notes.strip()
    ))
    project.status_message = f"Successfully added {quantity_val}x {part_name}."
    return project_dashboard(state)

@route
def calculator_route(state: State) -> Page:
    """
    Displays the active project's budget and weight limits compared to the accumulated 
    totals from the inventory, and provides a form to update the limits.
    """
    project = get_current_project(state)
    total_cost = sum(p.cost * p.quantity for p in project.parts)
    total_weight = sum(p.weight * p.quantity for p in project.parts)
    
    budget_status = "🔴 WARNING: Budget Exceeded!" if total_cost > project.budget else "✅ Budget is within limits."
    weight_status = "🔴 WARNING: Weight Exceeded!" if total_weight > project.max_weight else "✅ Weight is within limits."

    return Page(
        state,
        [
            Header(f"💰 Calculator & Limits: {project.name}"),
            Div([Text(budget_status)]),
            Div([Text(weight_status)]),
            Text(""),
            Div([Text("CURRENT METRICS:")]),
            Div([Text(f"  • Total Expenditure: ${total_cost} / ${project.budget}")]),
            Div([Text(f"  • Total Weight: {total_weight} lbs / {project.max_weight} lbs")]),
            Text(""),
            Div([Text("UPDATE LIMITS:")]),
            Div([Text("New Budget ($): "), TextBox("new_budget", str(project.budget))]),
            Div([Text("New Weight Limit (lbs): "), TextBox("new_weight", str(project.max_weight))]),
            Div([Button("Update Limits", update_limits_action)]),
            Text(""), Text(""),
            Div([Button("🔙 Back to Dashboard", project_dashboard)])
        ]
    )

@route
def update_limits_action(state: State, new_budget: str, new_weight: str) -> Page:
    """
    Validates and updates the budget and maximum weight limits for the active project.
    """
    project = get_current_project(state)
    try: project.budget = float(new_budget)
    except ValueError: pass
    try: project.max_weight = float(new_weight)
    except ValueError: pass
    return calculator_route(state)

@route
def about_route(state: State) -> Page:
    """
    Renders an informational page describing the purpose and usage of the application.
    """
    return Page(
        state,
        [
            Header("ℹ️ About This Tool"),
            Text(""),
            Div([Text("This site is a place where engineers working on projects can ")]),
            Div([Text("input their required materials and tools to get a total ")]),
            Div([Text("cost, weight, and other stats about their project.")]),
            Text(""), Text(""),
            Div([Button("🔙 Back to Projects Hub", index)])
        ]
    )

# --- 4. Unit Testing Block ---
def run_tests() -> None:
    """
    Executes automated unit tests via bakery assertions to verify core state 
    mutations and action functions behave correctly.
    """
    test_state = State(projects=[Project("Alpha", [], 100, 50, "All", "Name (A-Z)", "", "", "", True)], 
                       current_project_name="Alpha", global_message="", total_projects_created=1)
    assert_equal(get_current_project(test_state).name, "Alpha")

    new_state = State([], "", "", 0)
    create_project_action(new_state, "Beta")
    assert_equal(len(new_state.projects), 1)
    
    open_project_action(test_state, "Charlie")
    assert_equal(test_state.current_project_name, "Charlie")

    test_state.current_project_name = "Alpha"
    update_limits_action(test_state, "5000.5", "150.0")
    assert_equal(test_state.projects[0].budget, 5000.5)
    assert_equal(test_state.projects[0].max_weight, 150.0)

run_tests()

# --- 5. Initial State & Server Start ---
initial_state = State(
    projects=[], current_project_name="", 
    global_message="Welcome! Select or create a project to begin.", total_projects_created=0
)
start_server(initial_state)
