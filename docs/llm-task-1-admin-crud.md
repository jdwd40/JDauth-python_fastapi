# LLM Task 1: Admin CRUD Operations

## 🎯 **Task Overview**
Implement complete CRUD operations for admin user management. This is the **highest priority** task that enables admins to create, read, update, and delete users through dedicated API endpoints.

## 📋 **Context: What You're Building**
You're working on a FastAPI authentication app with JWT-based auth. The app already has:
- User registration/login
- Basic user profile management  
- Admin user listing (`GET /users`)
- MVC architecture with controllers, services, routes
- Comprehensive test coverage

**What's Missing**: Admin endpoints to CREATE, UPDATE, DELETE users.

## 🏗️ **Current Architecture Overview**
```
app/
├── controllers/
│   ├── auth_controller.py      # ✅ Exists
│   └── user_controller.py      # ✅ Exists (has get_user_list for admins)
├── services/
│   └── user_service.py         # ✅ Exists (has all CRUD functions!)
├── routes/
│   ├── auth.py                 # ✅ Exists  
│   └── user.py                 # ✅ Exists (has admin_router with GET /users)
├── schemas/
│   └── user.py                 # ✅ Exists (UserCreate, UserUpdate, UserResponse)
├── models/
│   └── user.py                 # ✅ Exists (User model)
└── utils/
    └── dependencies.py         # ✅ Exists (has require_admin dependency)
```

## 🎯 **Your Specific Tasks**

### **Task 1A: Add Admin Create User Endpoint**
- [ ] **Add route**: `POST /admin/users` in `app/routes/user.py` 
- [ ] **Add controller method**: `AdminUserController.create_user_as_admin()` in `app/controllers/user_controller.py`
- [ ] **Use existing service**: `user_service.create_user()` (already exists!)
- [ ] **Schema**: Use existing `UserCreate` schema
- [ ] **Dependencies**: Use existing `require_admin` dependency
- [ ] **Tests**: Add tests in `tests/test_routes/test_user_routes.py`

### **Task 1B: Add Admin Get Single User Endpoint**  
- [ ] **Add route**: `GET /admin/users/{user_id}` in `app/routes/user.py`
- [ ] **Add controller method**: `AdminUserController.get_user_details()`
- [ ] **Use existing service**: `user_service.get_user_by_id()` (already exists!)
- [ ] **Schema**: Use existing `UserResponse` schema
- [ ] **Error handling**: 404 if user not found
- [ ] **Tests**: Add comprehensive tests

### **Task 1C: Add Admin Update User Endpoint**
- [ ] **Add route**: `PUT /admin/users/{user_id}` in `app/routes/user.py`
- [ ] **Add controller method**: `AdminUserController.update_user_as_admin()`
- [ ] **Use existing service**: `user_service.update_user()` (already exists!)
- [ ] **Schema**: Use existing `UserUpdate` schema
- [ ] **Business logic**: Prevent admin from demoting themselves (future-proofing)
- [ ] **Tests**: Add comprehensive tests

### **Task 1D: Add Admin Delete User Endpoint**
- [ ] **Add route**: `DELETE /admin/users/{user_id}` in `app/routes/user.py`
- [ ] **Add controller method**: `AdminUserController.delete_user_as_admin()`
- [ ] **Use existing service**: `user_service.delete_user()` (already exists!)
- [ ] **Business logic**: Prevent admin from deleting themselves
- [ ] **Response**: Return success confirmation
- [ ] **Tests**: Add comprehensive tests

## 💡 **Key Implementation Notes**

### **1. Service Layer is Ready!**
The `user_service.py` already has all the CRUD functions you need:
- ✅ `create_user(db, user_data)` 
- ✅ `get_user_by_id(db, user_id)`
- ✅ `update_user(db, user_id, user_data)`
- ✅ `delete_user(db, user_id)`

### **2. Admin Router Pattern**
Follow the existing pattern in `app/routes/user.py`:
```python
# Add to existing admin_router (line ~132)
admin_router = APIRouter(tags=["User Administration"])

@admin_router.post("/admin/users", response_model=UserResponse)
def create_user_as_admin(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),  # Use existing dependency!
    db: Session = Depends(get_db)
):
    # Call controller method
```

### **3. Controller Pattern**
Add methods to existing `UserController` class in `app/controllers/user_controller.py`:
```python
def create_user_as_admin(self, db: Session, admin_user: User, user_data: UserCreate) -> UserResponse:
    """Admin creates a new user."""
    try:
        new_user = user_service.create_user(db, user_data)  # Use existing service!
        return UserResponse.model_validate(new_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### **4. Safety Checks to Add**
```python
# In delete/update methods, add:
if user_id == admin_user.id:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot modify your own admin account"
    )
```

## 🧪 **Testing Strategy**

### **Test File**: `tests/test_routes/test_user_routes.py`
Add test methods to existing `TestUserRoutes` class:

```python
def test_admin_create_user_success(self, admin_client):
    """Test admin can create new user."""
    client, admin_user = admin_client
    
    user_data = {
        "username": "newuser",
        "password": "password123"
    }
    response = client.post("/api/admin/users", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data

def test_admin_create_user_forbidden_non_admin(self, authenticated_client):
    """Test regular user cannot create users."""
    client, user = authenticated_client
    
    user_data = {"username": "test", "password": "password123"}
    response = client.post("/api/admin/users", json=user_data)
    
    assert response.status_code == 403
```

## 📁 **Files You'll Need to Modify**

### **1. `app/routes/user.py`**
- Add 4 new endpoints to existing `admin_router`
- Import any additional dependencies if needed

### **2. `app/controllers/user_controller.py`** 
- Add 4 new methods to existing `UserController` class
- Follow existing patterns for error handling

### **3. `tests/test_routes/test_user_routes.py`**
- Add ~12-16 new test methods to existing `TestUserRoutes` class
- Test success cases, error cases, and authorization

## 🎯 **Success Criteria**
- [ ] All 4 admin CRUD endpoints working
- [ ] Proper error handling (400, 403, 404, 500)
- [ ] Admin authorization enforced
- [ ] Self-modification prevention
- [ ] Comprehensive test coverage
- [ ] All existing tests still pass

## 🚀 **Expected Outcome**
After this task, admins will be able to:
- Create new users via API
- View any user's details  
- Update any user's information
- Delete users (with safety checks)

This provides the core admin functionality needed for the frontend GUI.

## 📚 **Context Files to Reference**
- `app/routes/user.py` - See existing admin_router pattern
- `app/controllers/user_controller.py` - See existing controller patterns
- `app/services/user_service.py` - See available CRUD functions
- `app/utils/dependencies.py` - See require_admin dependency
- `tests/test_routes/test_user_routes.py` - See existing test patterns

## ⏱️ **Estimated Time**: 4-6 hours
- 2 hours: Implementation
- 2 hours: Testing  
- 1-2 hours: Refinement and edge cases
