from drafter import *
from dataclasses import dataclass
from bakery import assert_equal # Imported for the test suite

# --- 1. Dataclasses ---

@dataclass
class Part:
    name: str 
    material: str 
    weight: float 
    cost: float 
    quantity: int
    purchased: bool = False 

@dataclass
class Project:
    name: str
    parts: list[Part]
    budget: float
    current_filter: str
    current_sort: str
    status_message: str
    editing_part_name: str = ""

@dataclass
class State:
    projects: list[Project]
    current_project_name: str
    global_message: str
    total_projects_created: int 

# --- Helper Function ---
def get_current_project(state: State) -> Project:
    """Helper to retrieve the currently active project object."""
    for p in state.projects:
        if p.name == state.current_project_name:
            return p
    return None

# --- 2. Routes & Pages ---

@route
def index(state: State) -> Page:
    """
    Projects Hub: Main landing page to manage multiple projects.
    Note: This route returns UI components and is difficult to unit test in isolation.
    """
    content = [
        Header("Projects Hub"),
        Text(state.global_message)
    ]
    
    if len(state.projects) > 0:
        project_names = [p.name for p in state.projects]
        
        if state.current_project_name in project_names:
            default_selection = state.current_project_name
        else:
            default_selection = project_names[0]
            
        content.extend([
            Text("Open an Existing Project:"),
            SelectBox("selected_project", project_names, default_selection),
            Button("Open Project", open_project_action),
            Text("---")
        ])
    else:
        content.append(Text("No projects yet. Create one below!"))
        
    content.extend([
        Text("Create a New Project:"),
        Text("Project Name:"),
        TextBox("new_project_name", ""),
        Button("Create Project", create_project_action),
        Button("About", about_route),
        Text(f"Total Projects Created Lifetime: {state.total_projects_created}")
    ])
    
    return Page(state, content)

@route
def create_project_action(state: State, new_project_name: str) -> Page:
    """Handles the creation of a new project and modifies 4 State fields."""
    if new_project_name == "" or new_project_name.isspace():
        state.global_message = "Error: Project name cannot be empty."
        return index(state)
        
    for p in state.projects:
        if p.name == new_project_name:
            state.global_message = f"Error: Project '{new_project_name}' exists."
            return index(state)
            
    new_project = Project(
        name=new_project_name,
        parts=[],
        budget=1000.0,
        current_filter="All",
        current_sort="Name (A-Z)",
        status_message="",
        editing_part_name=""
    )
    
    state.projects.append(new_project)
    state.current_project_name = new_project_name
    state.global_message = ""
    state.total_projects_created += 1
    
    return project_dashboard(state)

@route
def open_project_action(state: State, selected_project: str) -> Page:
    """Sets the selected project as active and navigates to its dashboard."""
    state.current_project_name = selected_project
    state.global_message = ""
    return project_dashboard(state)

@route
def project_dashboard(state: State) -> Page:
    """
    Project Dashboard: Overview for a specific project.
    Note: This route returns UI components and is difficult to unit test in isolation.
    """
    project = get_current_project(state)
    if not project:
        return index(state)
        
    total_parts = sum(part.quantity for part in project.parts)
    total_weight = sum(part.weight * part.quantity for part in project.parts)
    total_cost = sum(part.cost * part.quantity for part in project.parts)
        
    return Page(
        state,
        [
            Header(f"Dashboard: {project.name}"),
            Text(project.status_message),
            Text(f"Total Individual Parts: {total_parts}"),
            Text(f"Combined Weight: {total_weight} lbs"),
            Text(f"Current Budget Health: ${total_cost} / ${project.budget}"),
            Button("View Inventory", inventory_route),
            Button("Add New Part", add_part_form_route),
            Button("Budget Calculator", calculator_route),
            Button("Back to Projects Hub", index)
        ]
    )

@route
def inventory_route(state: State) -> Page:
    """
    Inventory Page: Displays components, expenditures, and allows editing/removing.
    Note: This route returns UI components and is difficult to unit test in isolation.
    """
    project = get_current_project(state)
    
    # Calculate costs for the header
    total_spent = sum(p.cost * p.quantity for p in project.parts if p.purchased)
    total_projected = sum(p.cost * p.quantity for p in project.parts)
    
    content = [
        Header(f"Inventory: {project.name}"),
        Text(f"Total Amount Spent (Purchased Items): ${total_spent}"),
        Text(f"Total Projected Expenditure (All Items): ${total_projected}"),
        Text(f"Total Project Budget: ${project.budget}"),
        Text("---"),
        Button("Back to Dashboard", project_dashboard),
        Text(project.status_message),
        Text("---")
    ]

    if not project.parts:
        content.append(Text("No parts have been added to this project yet."))
    else:
        for p in project.parts:
            status = "Purchased" if p.purchased else "Not Purchased"
            total_weight = p.weight * p.quantity
            total_cost = p.cost * p.quantity
            
            content.append(
                Text(f"• {p.quantity}x {p.name} ({p.material}): "
                     f"{total_weight} lbs total, ${total_cost} total [{status}]")
            )

        part_names = [p.name for p in project.parts]
        
        # New Purchase Status Area and existing Edit/Remove Area
        content.extend([
            Text("---"),
            Text("Update Purchase Status:"),
            SelectBox("status_part_name", part_names, part_names[0]),
            CheckBox("is_purchased_status", True),
            Button("Set Status", update_status_action),
            Text("---"),
            Text("Manage an Existing Part/Material:"),
            SelectBox("selected_part_name", part_names, part_names[0]),
            Button("Edit Selected Part", edit_part_setup_action),
            Button("Remove Selected Part", remove_part_action) 
        ])

    return Page(state, content)

@route
def update_status_action(state: State, status_part_name: str, is_purchased_status: bool) -> Page:
    """Updates the purchased status of a selected part directly from the inventory page."""
    project = get_current_project(state)
    for p in project.parts:
        if p.name == status_part_name:
            p.purchased = is_purchased_status
            status_word = "Purchased" if is_purchased_status else "Not Purchased"
            project.status_message = f"Success: '{p.name}' is now marked as {status_word}."
            break
    return inventory_route(state)

@route
def remove_part_action(state: State, selected_part_name: str) -> Page:
    """Deletes a part from the active project."""
    project = get_current_project(state)
    
    updated_parts = []
    for p in project.parts:
        if p.name != selected_part_name:
            updated_parts.append(p)
            
    project.parts = updated_parts
    project.status_message = f"Success: '{selected_part_name}' removed."
    return inventory_route(state)

@route
def edit_part_setup_action(state: State, selected_part_name: str) -> Page:
    """Prepares the state for editing a specific part."""
    project = get_current_project(state)
    project.editing_part_name = selected_part_name
    project.status_message = ""
    return edit_part_page(state)

@route
def edit_part_page(state: State) -> Page:
    """
    Displays a form pre-filled with the selected part's existing details.
    Note: This route returns UI components and is difficult to unit test in isolation.
    """
    project = get_current_project(state)
    
    part_to_edit = None
    for p in project.parts:
        if p.name == project.editing_part_name:
            part_to_edit = p
            break
            
    if not part_to_edit:
        project.status_message = "Error: Could not find the selected part."
        return inventory_route(state)

    return Page(
        state,
        [
            Header(f"Edit Part: {part_to_edit.name}"),
            Text(project.status_message),
            
            Text("Part Name:"),
            TextBox("part_name", part_to_edit.name),
            Text("Quantity:"),
            TextBox("part_quantity", str(part_to_edit.quantity)),
            Text("Weight per item (lbs):"),
            TextBox("part_weight", str(part_to_edit.weight)),
            Text("Cost per item ($):"),
            TextBox("part_cost", str(part_to_edit.cost)),
            
            Text("Material:"),
            SelectBox("part_material", ["Aluminum", "Steel", "Brass", "Wood", "Other"], 
                      part_to_edit.material),
            
            Button("Save Changes", update_part_action),
            Button("Cancel", inventory_route)
        ]
    )

@route
def update_part_action(state: State, part_name: str, part_quantity: str, 
                       part_weight: str, part_cost: str, part_material: str) -> Page:
    """Processes modifications to an existing part."""
    project = get_current_project(state)
    
    if part_name == "" or part_name.isspace():
        project.status_message = "Error: Part name cannot be empty."
        return edit_part_page(state)
    
    try:
        weight_val = float(part_weight)
        cost_val = float(part_cost)
        quantity_val = int(part_quantity)
    except ValueError:
        project.status_message = "Error: Invalid number entries."
        return edit_part_page(state)

    for p in project.parts:
        if p.name == project.editing_part_name:
            p.name = part_name
            p.material = part_material
            p.weight = weight_val
            p.cost = cost_val
            p.quantity = quantity_val
            # purchased status remains unchanged here
            break
            
    project.status_message = f"Success: {part_name} has been updated."
    project.editing_part_name = "" 
    
    return inventory_route(state)

@route
def add_part_form_route(state: State) -> Page:
    """
    Add Part Form: Adds components to the current project.
    Note: This route returns UI components and is difficult to unit test in isolation.
    """
    project = get_current_project(state)
    return Page(
        state,
        [
            Header(f"Add Component to {project.name}"),
            Text(project.status_message),
            
            Text("Part Name:"),
            TextBox("part_name", ""),
            Text("Quantity:"),
            TextBox("part_quantity", ""),
            Text("Weight per item (lbs):"),
            TextBox("part_weight", ""),
            Text("Cost per item ($):"),
            TextBox("part_cost", ""),
            
            Text("Material:"),
            SelectBox("part_material", ["Aluminum", "Steel", "Brass", "Wood", "Other"], 
                      "Aluminum"),
            
            Button("Save Part", add_part_action),
            Button("Cancel", project_dashboard)
        ]
    )

@route
def add_part_action(state: State, part_name: str, part_quantity: str, 
                    part_weight: str, part_cost: str, part_material: str) -> Page:
    """Processes the submitted part form into the active project."""
    project = get_current_project(state)
    
    if part_name == "" or part_name.isspace():
        project.status_message = "Error: Part name cannot be empty."
        return add_part_form_route(state)
    
    try:
        weight_val = float(part_weight)
        cost_val = float(part_cost)
        quantity_val = int(part_quantity)
    except ValueError:
        project.status_message = "Error: Number error in form inputs."
        return add_part_form_route(state)

    new_part = Part(
        name=part_name, 
        material=part_material, 
        weight=weight_val, 
        cost=cost_val, 
        quantity=quantity_val,
        purchased=False # Defaults to False, user can update on Inventory page
    )
    
    project.parts.append(new_part)
    project.status_message = f"Success: Added {quantity_val}x {part_name}."
    
    return project_dashboard(state)

@route
def calculator_route(state: State) -> Page:
    """
    Calculator Page: Checks the current project's budget.
    Note: This route returns UI components and is difficult to unit test in isolation.
    """
    project = get_current_project(state)
    
    total_cost = sum(p.cost * p.quantity for p in project.parts)
    
    if total_cost > project.budget:
        project.status_message = "WARNING: Maximum allowable budget exceeded!"
    else:
        project.status_message = "Budget is currently within limits."

    return Page(
        state,
        [
            Header(f"Calculator: {project.name}"),
            Text(project.status_message),
            Text(f"Total Expenditure: ${total_cost}"),
            Text(f"Current Budget: ${project.budget}"),
            Text("Update Budget ($):"),
            TextBox("new_budget", str(project.budget)),
            Button("Update Budget Limit", update_budget_action),
            Button("Back to Dashboard", project_dashboard)
        ]
    )

@route
def update_budget_action(state: State, new_budget: str) -> Page:
    """Processes a new budget limit for the current project."""
    project = get_current_project(state)
    try:
        project.budget = float(new_budget)
    except ValueError:
        pass
    return calculator_route(state)

@route
def about_route(state: State) -> Page:
    """
    About Page.
    Note: This route returns UI components and is difficult to unit test in isolation.
    """
    return Page(
        state,
        [
            Header("About This Tool"),
            Text("This site is a place where engineers working on projects can "
                 "input their required materials and tools to get a total "
                 "cost, weight, and other stats about their project."),
            Button("Back to Projects Hub", index)
        ]
    )


# --- 4. Unit Testing Block ---

def run_tests() -> None:
    """Tests the critical data mutators and logic paths where possible."""
    
    # Test 1: Helper function
    test_state = State(projects=[Project("Alpha", [], 100, "All", "Name (A-Z)", "", "")], 
                       current_project_name="Alpha", global_message="", total_projects_created=1)
    
    assert_equal(get_current_project(test_state).name, "Alpha")

    # Test 2: create_project_action modifies 4 distinct state variables
    new_state = State([], "", "", 0)
    create_project_action(new_state, "Beta")
    
    assert_equal(len(new_state.projects), 1)
    assert_equal(new_state.current_project_name, "Beta")
    assert_equal(new_state.total_projects_created, 1)
    assert_equal(new_state.global_message, "")

    # Test 3: open_project_action updates active project
    open_project_action(test_state, "Charlie")
    assert_equal(test_state.current_project_name, "Charlie")

    # Test 4: update_budget_action updates float limits correctly
    test_state.current_project_name = "Alpha"
    update_budget_action(test_state, "5000.5")
    assert_equal(test_state.projects[0].budget, 5000.5)
    
    # Test 5: update_status_action dynamically updates purchased status
    test_state.projects[0].parts.append(Part("Nail", "Steel", 0.1, 0.5, 100, False))
    update_status_action(test_state, "Nail", True)
    assert_equal(test_state.projects[0].parts[0].purchased, True)
    
    # Test 6: remove_part_action handles part deletion dynamically
    remove_part_action(test_state, "Nail")
    assert_equal(len(test_state.projects[0].parts), 0)

# Run assertions before app launch
run_tests()


# --- 5. Initial State & Server Start ---

initial_state = State(
    projects=[], 
    current_project_name="", 
    global_message="Welcome! Please select or create a project to begin.",
    total_projects_created=0
)

start_server(initial_state)
