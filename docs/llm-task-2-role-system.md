# LLM Task 2: Enhanced Role Management System

## 🎯 **Task Overview**
Upgrade the current basic admin detection system to a proper role-based system with database fields, proper authentication, and user status management.

## 📋 **Context: Current Role System Issues**
The app currently uses a **hacky admin detection**:
```python
# Current implementation in user_controller.py
def _is_admin_user(self, user: User) -> bool:
    if hasattr(user, 'is_admin'):
        return getattr(user, 'is_admin', False)
    # Fallback: check username (temporary for testing)
    return user.username == 'admin'
```

**Problems:**
- No role field in database
- No user status (active/inactive) management
- Inconsistent admin detection
- No proper role assignment

## 🏗️ **Current State Analysis**

### **Database Model** (`app/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Missing: role and is_active fields!
```

### **Dependencies** (`app/utils/dependencies.py`)
```python
def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    # Currently has placeholder implementation
    if hasattr(current_user, 'is_admin') and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
```

## 🎯 **Your Specific Tasks**

### **Task 2A: Database Schema Enhancement**
- [ ] **Update User Model** in `app/models/user.py`:
  ```python
  role = Column(String(20), default="user", nullable=False)  # "admin" or "user"
  is_active = Column(Boolean, default=True, nullable=False)
  ```
- [ ] **Create Alembic Migration**:
  ```bash
  alembic revision --autogenerate -m "Add role and is_active fields to users"
  alembic upgrade head
  ```
- [ ] **Update Database**: Run migration on existing database

### **Task 2B: Create Role Management Schemas**
- [ ] **Add Role Enum** to `app/schemas/user.py`:
  ```python
  from enum import Enum
  
  class UserRole(str, Enum):
      ADMIN = "admin"
      USER = "user"
  ```
- [ ] **Update UserResponse Schema**: Include role and is_active fields
- [ ] **Create AdminUserCreate Schema**: Allow role assignment during creation
- [ ] **Create AdminUserUpdate Schema**: Allow role changes

### **Task 2C: Update Service Layer**
- [ ] **Update `user_service.py`**:
  - Modify `create_user()` to accept optional role parameter
  - Add role validation functions
  - Add user status management functions
- [ ] **Add New Service Functions**:
  ```python
  def set_user_role(db: Session, user_id: int, role: UserRole) -> User
  def activate_user(db: Session, user_id: int) -> User  
  def deactivate_user(db: Session, user_id: int) -> User
  def get_users_by_role(db: Session, role: UserRole) -> List[User]
  ```

### **Task 2D: Update Authentication Logic**
- [ ] **Fix `require_admin` dependency** in `app/utils/dependencies.py`:
  ```python
  def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
      if current_user.role != "admin":
          raise HTTPException(status_code=403, detail="Admin access required")
      if not current_user.is_active:
          raise HTTPException(status_code=403, detail="Account is inactive")
      return current_user
  ```
- [ ] **Update `get_current_active_user`**: Check `is_active` field
- [ ] **Update Login Logic**: Check user status in authentication

### **Task 2E: Update Controllers**
- [ ] **Update `UserController`**:
  - Fix `_is_admin_user()` method to use role field
  - Add role management methods
  - Add user status management methods
- [ ] **Add Controller Methods**:
  ```python
  def change_user_role(self, db: Session, admin_user: User, user_id: int, new_role: UserRole)
  def toggle_user_status(self, db: Session, admin_user: User, user_id: int, active: bool)
  ```

### **Task 2F: Create Admin Role Management Endpoints**
- [ ] **Add Routes** to `app/routes/user.py`:
  ```python
  @admin_router.patch("/admin/users/{user_id}/role")
  def change_user_role(...)
  
  @admin_router.patch("/admin/users/{user_id}/activate") 
  def activate_user(...)
  
  @admin_router.patch("/admin/users/{user_id}/deactivate")
  def deactivate_user(...)
  ```

## 💡 **Key Implementation Details**

### **1. Database Migration Script**
```python
# In the generated migration file
def upgrade():
    # Add role column with default 'user'
    op.add_column('users', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
    # Add is_active column with default True
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    # Create an admin user if none exists
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET role = 'admin' WHERE username = 'admin'"
    )
```

### **2. Schema Updates**
```python
# Updated UserResponse in app/schemas/user.py
class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole  # NEW
    is_active: bool  # NEW
    created_at: datetime
    
class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER  # NEW - defaults to user
    is_active: bool = True  # NEW
```

### **3. Safety Checks**
```python
# Prevent admin from demoting themselves
def change_user_role(self, db: Session, admin_user: User, user_id: int, new_role: UserRole):
    if user_id == admin_user.id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=400, 
            detail="Cannot remove admin role from yourself"
        )
    # ... rest of implementation
```

## 🧪 **Testing Strategy**

### **Test Categories**
1. **Database Migration Tests**: Verify schema changes
2. **Role Assignment Tests**: Test role changes and validation
3. **Authentication Tests**: Test role-based access control  
4. **Status Management Tests**: Test activate/deactivate functionality
5. **Safety Tests**: Test self-modification prevention

### **Key Test Cases**
```python
def test_admin_can_change_user_role(self, admin_client):
    """Test admin can change user roles."""
    
def test_admin_cannot_demote_self(self, admin_client):
    """Test admin cannot remove own admin role."""
    
def test_inactive_user_cannot_login(self, client):
    """Test deactivated user cannot authenticate."""
    
def test_role_based_access_control(self, authenticated_client):
    """Test regular user cannot access admin endpoints."""
```

## 📁 **Files You'll Need to Modify**

### **1. Database & Models**
- `app/models/user.py` - Add role and is_active fields
- Create new Alembic migration file
- `seed_database.py` - Update to create admin user with proper role

### **2. Schemas**  
- `app/schemas/user.py` - Add role enum and update schemas

### **3. Services**
- `app/services/user_service.py` - Add role management functions

### **4. Dependencies & Auth**
- `app/utils/dependencies.py` - Fix admin detection
- `app/services/auth_service.py` - Update login to check is_active

### **5. Controllers & Routes**
- `app/controllers/user_controller.py` - Update admin detection and add role methods
- `app/routes/user.py` - Add role management endpoints

### **6. Tests**
- `tests/test_models/` - Add model tests for new fields
- `tests/test_services/` - Add role management service tests  
- `tests/test_routes/` - Add role management endpoint tests
- `tests/conftest.py` - Update fixtures to handle roles

## 🎯 **Success Criteria**
- [ ] Database has role and is_active fields
- [ ] Proper role-based authentication
- [ ] Admin can assign/change user roles
- [ ] Admin can activate/deactivate users
- [ ] Inactive users cannot login
- [ ] Safety checks prevent admin self-demotion
- [ ] All tests pass with new role system
- [ ] Existing functionality unchanged

## 🚀 **Expected Outcome**
After this task:
- Proper role-based access control system
- Database-driven role assignments  
- User status management (active/inactive)
- Foundation for future role expansions
- Secure admin privilege management

## 📚 **Context Files to Reference**
- `app/models/user.py` - Current User model
- `app/utils/dependencies.py` - Current admin detection
- `app/schemas/user.py` - Current user schemas
- `alembic/` directory - Migration examples
- `tests/test_models/` - Model testing patterns

## ⏱️ **Estimated Time**: 6-8 hours
- 2 hours: Database migration and model updates
- 2 hours: Service and schema updates  
- 2 hours: Authentication and controller updates
- 2 hours: Testing and validation
