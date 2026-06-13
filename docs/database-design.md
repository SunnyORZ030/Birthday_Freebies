## Initial Database Design

### users
- id: UUID, Primary Key
- email: VARCHAR(255), Unique, Not Null
- password_hash: VARCHAR(255), Not Null
- display_name: VARCHAR(100), Nullable
- birthday_month: INTEGER, Nullable
- birthday_day: INTEGER, Nullable
- created_at: TIMESTAMP, Not Null
- updated_at: TIMESTAMP, Not Null

### restaurants
- id: UUID, Primary Key
- name: VARCHAR(255), Not Null
- website_url: TEXT, Nullable
- logo_url: TEXT, Nullable
- category: VARCHAR(100), Nullable
- created_at: TIMESTAMP, Not Null
- updated_at: TIMESTAMP, Not Null

### offers
- id: UUID, Primary Key
- restaurant_id: UUID, Foreign Key → restaurants.id, Not Null
- title: VARCHAR(255), Not Null
- description: TEXT, Not Null
- offer_type: VARCHAR(100), Nullable
- redemption_requirement: TEXT, Nullable
- expiration_policy: TEXT, Nullable
- is_active: BOOLEAN, Not Null, Default True
- source_url: TEXT, Nullable
- created_at: TIMESTAMP, Not Null
- updated_at: TIMESTAMP, Not Null

### favorites
- id: UUID, Primary Key
- user_id: UUID, Foreign Key → users.id, Not Null
- offer_id: UUID, Foreign Key → offers.id, Not Null
- created_at: TIMESTAMP, Not Null
- Unique constraint: user_id + offer_id


## Initial API Endpoints

### Offers

- `GET /api/v1/offers`
- `GET /api/v1/offers/{offer_id}`

### Restaurants

- `GET /api/v1/restaurants`
- `GET /api/v1/restaurants/{restaurant_id}`
- `GET /api/v1/restaurants/{restaurant_id}/offers`

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Favorites

- `GET /api/v1/favorites`
- `POST /api/v1/favorites/{offer_id}`
- `DELETE /api/v1/favorites/{offer_id}`