# LLM Task 3: Enhanced User Management Features

## 🎯 **Task Overview**
Add enhanced user management features including search/filtering, admin dashboard statistics, and improved user experience features. This builds on the CRUD operations and role system from Tasks 1 & 2.

## 📋 **Context: What You're Building**
You're adding "nice-to-have" features that make the admin interface more powerful and user-friendly:
- User search and filtering capabilities
- Admin dashboard with statistics
- Bulk operations support
- Enhanced user listing with sorting

**Prerequisites**: Tasks 1 (Admin CRUD) and 2 (Role System) must be completed first.

## 🏗️ **Current State After Previous Tasks**
- ✅ Admin CRUD operations (create, read, update, delete users)
- ✅ Role-based system (admin/user roles, active/inactive status)
- ✅ Proper authentication and authorization
- ✅ Basic user listing with pagination (`GET /users`)

## 🎯 **Your Specific Tasks**

### **Task 3A: Advanced User Search & Filtering**

#### **3A.1: Search Endpoint**
- [ ] **Add Route**: `GET /admin/users/search` in `app/routes/user.py`
- [ ] **Query Parameters**:
  ```python
  @admin_router.get("/admin/users/search")
  def search_users(
      q: Optional[str] = Query(None, description="Search query (username)"),
      role: Optional[UserRole] = Query(None, description="Filter by role"),
      is_active: Optional[bool] = Query(None, description="Filter by status"),
      created_after: Optional[datetime] = Query(None, description="Created after date"),
      created_before: Optional[datetime] = Query(None, description="Created before date"),
      sort_by: Optional[str] = Query("created_at", description="Sort field"),
      sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
      skip: int = Query(0, ge=0),
      limit: int = Query(50, ge=1, le=100)
  ):
  ```

#### **3A.2: Search Service Functions**
- [ ] **Add to `user_service.py`**:
  ```python
  def search_users(
      db: Session, 
      query: Optional[str] = None,
      role: Optional[UserRole] = None,
      is_active: Optional[bool] = None,
      created_after: Optional[datetime] = None,
      created_before: Optional[datetime] = None,
      sort_by: str = "created_at",
      sort_order: str = "desc",
      skip: int = 0,
      limit: int = 50
  ) -> List[User]:
  ```
- [ ] **Implementation**: Use SQLAlchemy filters and sorting
- [ ] **Add Database Indexes**: For search performance

#### **3A.3: Enhanced User Listing**
- [ ] **Update existing `GET /users` endpoint**: Add optional filtering parameters
- [ ] **Maintain backward compatibility**: Default behavior unchanged
- [ ] **Add sorting options**: username, created_at, role, status

### **Task 3B: Admin Dashboard Statistics**

#### **3B.1: Dashboard Endpoint**
- [ ] **Add Route**: `GET /admin/dashboard/stats` in `app/routes/user.py`
- [ ] **Response Schema**: Create `DashboardStats` schema
- [ ] **Statistics to Include**:
  ```python
  {
      "total_users": 150,
      "active_users": 142,
      "inactive_users": 8,
      "admin_users": 3,
      "regular_users": 147,
      "recent_registrations": {
          "today": 5,
          "this_week": 23,
          "this_month": 67
      },
      "user_growth": [
          {"date": "2024-01-01", "count": 10},
          {"date": "2024-01-02", "count": 12},
          # ... last 30 days
      ]
  }
  ```

#### **3B.2: Analytics Service**
- [ ] **Create `app/services/analytics_service.py`**:
  ```python
  def get_user_statistics(db: Session) -> Dict[str, Any]:
      """Get comprehensive user statistics."""
  
  def get_user_growth_data(db: Session, days: int = 30) -> List[Dict]:
      """Get user registration growth over time."""
  
  def get_role_distribution(db: Session) -> Dict[str, int]:
      """Get count of users by role."""
  ```
- [ ] **Efficient Queries**: Use SQLAlchemy aggregation functions
- [ ] **Caching Consideration**: Add TODO for Redis caching

#### **3B.3: Dashboard Controller**
- [ ] **Create `app/controllers/dashboard_controller.py`**:
  ```python
  class DashboardController:
      def get_admin_dashboard_stats(self, db: Session, admin_user: User) -> DashboardStatsResponse:
          """Get dashboard statistics for admin."""
  ```

### **Task 3C: Bulk Operations Support**

#### **3C.1: Bulk User Status Changes**
- [ ] **Add Routes**:
  ```python
  @admin_router.patch("/admin/users/bulk/activate")
  def bulk_activate_users(user_ids: List[int], ...)
  
  @admin_router.patch("/admin/users/bulk/deactivate") 
  def bulk_deactivate_users(user_ids: List[int], ...)
  ```
- [ ] **Request Schema**: Create `BulkUserAction` schema
- [ ] **Response Schema**: Include success/failure counts

#### **3C.2: Bulk Service Functions**
- [ ] **Add to `user_service.py`**:
  ```python
  def bulk_update_user_status(
      db: Session, 
      user_ids: List[int], 
      is_active: bool
  ) -> Dict[str, List[int]]:
      """Bulk update user status. Returns success/failed IDs."""
  ```
- [ ] **Transaction Safety**: Use database transactions
- [ ] **Error Handling**: Continue on individual failures

### **Task 3D: Enhanced User Profile Features**

#### **3D.1: User Activity Tracking**
- [ ] **Add to User Model**: `last_login_at` field (optional)
- [ ] **Update Login Service**: Track login timestamps
- [ ] **Display in Admin Interface**: Show last login in user lists

#### **3D.2: User Export Functionality**
- [ ] **Add Route**: `GET /admin/users/export` 
- [ ] **Format Options**: CSV, JSON export
- [ ] **Filtering**: Apply same filters as search
- [ ] **Security**: Admin-only, rate-limited

## 💡 **Key Implementation Details**

### **1. Search Implementation**
```python
# In user_service.py
def search_users(db: Session, query: Optional[str] = None, **filters) -> List[User]:
    query_builder = db.query(User)
    
    # Text search
    if query:
        query_builder = query_builder.filter(User.username.ilike(f"%{query}%"))
    
    # Role filter
    if filters.get('role'):
        query_builder = query_builder.filter(User.role == filters['role'])
    
    # Status filter  
    if filters.get('is_active') is not None:
        query_builder = query_builder.filter(User.is_active == filters['is_active'])
    
    # Date range filters
    if filters.get('created_after'):
        query_builder = query_builder.filter(User.created_at >= filters['created_after'])
    
    # Sorting
    sort_field = getattr(User, filters.get('sort_by', 'created_at'))
    if filters.get('sort_order') == 'desc':
        query_builder = query_builder.order_by(sort_field.desc())
    else:
        query_builder = query_builder.order_by(sort_field.asc())
    
    return query_builder.offset(filters.get('skip', 0)).limit(filters.get('limit', 50)).all()
```

### **2. Dashboard Statistics**
```python
# In analytics_service.py
def get_user_statistics(db: Session) -> Dict[str, Any]:
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.role == "admin").count()
    
    # Recent registrations
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    today_count = db.query(User).filter(func.date(User.created_at) == today).count()
    week_count = db.query(User).filter(User.created_at >= week_ago).count()
    month_count = db.query(User).filter(User.created_at >= month_ago).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "admin_users": admin_users,
        "regular_users": total_users - admin_users,
        "recent_registrations": {
            "today": today_count,
            "this_week": week_count,
            "this_month": month_count
        }
    }
```

### **3. Bulk Operations**
```python
# In user_service.py
def bulk_update_user_status(db: Session, user_ids: List[int], is_active: bool) -> Dict[str, List[int]]:
    success_ids = []
    failed_ids = []
    
    for user_id in user_ids:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_active = is_active
                user.updated_at = datetime.now(timezone.utc)
                success_ids.append(user_id)
            else:
                failed_ids.append(user_id)
        except Exception:
            failed_ids.append(user_id)
    
    db.commit()
    return {"success": success_ids, "failed": failed_ids}
```

## 📋 **New Schemas Needed**

### **Create `app/schemas/analytics.py`**
```python
class DashboardStatsResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    admin_users: int
    regular_users: int
    recent_registrations: Dict[str, int]
    user_growth: Optional[List[Dict[str, Any]]] = None

class UserSearchFilters(BaseModel):
    q: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"

class BulkUserAction(BaseModel):
    user_ids: List[int] = Field(..., min_items=1, max_items=100)
    
class BulkActionResponse(BaseModel):
    success_count: int
    failed_count: int
    success_ids: List[int]
    failed_ids: List[int]
```

## 🧪 **Testing Strategy**

### **Test Categories**
1. **Search Tests**: Various search combinations and edge cases
2. **Dashboard Tests**: Statistics accuracy and performance
3. **Bulk Operations Tests**: Success/failure scenarios
4. **Performance Tests**: Large dataset handling
5. **Authorization Tests**: Admin-only access enforcement

### **Key Test Cases**
```python
def test_user_search_by_username(self, admin_client):
    """Test searching users by username."""

def test_user_search_with_filters(self, admin_client):
    """Test searching with multiple filters."""

def test_dashboard_statistics_accuracy(self, admin_client):
    """Test dashboard statistics are accurate."""

def test_bulk_activate_users(self, admin_client):
    """Test bulk user activation."""

def test_search_pagination_and_sorting(self, admin_client):
    """Test search with pagination and sorting."""
```

## 📁 **Files You'll Need to Create/Modify**

### **New Files**
- `app/services/analytics_service.py` - Dashboard statistics
- `app/controllers/dashboard_controller.py` - Dashboard controller
- `app/schemas/analytics.py` - Analytics schemas

### **Modified Files**
- `app/routes/user.py` - Add search, dashboard, bulk endpoints
- `app/services/user_service.py` - Add search and bulk functions
- `app/controllers/user_controller.py` - Add search and bulk methods
- `tests/test_routes/test_user_routes.py` - Add comprehensive tests
- `tests/test_services/test_user_service.py` - Add service tests

## 🎯 **Success Criteria**
- [ ] Advanced user search with multiple filters works
- [ ] Admin dashboard shows accurate statistics
- [ ] Bulk operations handle success/failure gracefully
- [ ] Search performance is acceptable (< 500ms for 1000+ users)
- [ ] All features are admin-only protected
- [ ] Comprehensive test coverage
- [ ] Backward compatibility maintained

## 🚀 **Expected Outcome**
After this task, admins will have:
- Powerful search and filtering capabilities
- Insightful dashboard with user statistics
- Efficient bulk operations for user management
- Enhanced user experience for admin tasks
- Foundation for future analytics features

## 📚 **Context Files to Reference**
- Previous task implementations (Tasks 1 & 2)
- `app/routes/user.py` - Existing endpoint patterns
- `app/services/user_service.py` - Existing service patterns
- `tests/test_routes/test_user_routes.py` - Testing patterns

## ⏱️ **Estimated Time**: 8-10 hours
- 3 hours: Search and filtering implementation
- 2 hours: Dashboard statistics
- 2 hours: Bulk operations
- 3 hours: Testing and refinement
