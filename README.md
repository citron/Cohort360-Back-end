# Cohort360 Back-end

## Installation

### Customize settings.py

```
cp cohort_back/example.settings.py cohort_back/settings.py
"${EDITOR:-vi}" cohort_back/settings.py
```

### Install requirements

```
pip install -r requirements.txt
```

### Create database tables

```
python manage.py makemigrations cohort
python manage.py migrate
```

### Load base data

```
python manage.py loaddata cohort/fixtures/data.json
```

## Details & Development

### Authentication

You can use two methods to authenticate users: simple or via LDAP (both need a user+password).

You will then be able to get a JSON Web Token (JWT) to further authenticate to other urls of this API.

1. The first step is to create a user using a signup view and by specifying if it is via simple or LDAP auth.
2. The user can now authenticate at `/api/jwt/` by specifying a `username` and a `password` in the request data. This will return a JSON response containing an access and a refresh token.
3. The user can now use its access token to browse other API urls by specifying it in the request authorization header ("Authorization: Bearer \<the-access-token-here\>").
4. When the access token expires, use the `/api/jwt/refresh` url by specifying the `refresh` token in the request data. This will return a JSON response containing a new access token.

