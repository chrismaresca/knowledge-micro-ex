from typing import Optional

# FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status, Response

# Firebase
from firebase_admin import auth, credentials, initialize_app, firestore

# Pydantic
from pydantic import BaseModel

credential = credentials.Certificate(cert='key.json')
initialize_app(credential=credential)

# Initialize Firestore client
db = firestore.client()


ROLE_HIERARCHY = {
    'free': 1,
    'basic': 2,
    'paid': 3,
    'premium': 4
}


class BaseUser(BaseModel):
    id: str
    email: str
    role: str


def fetch_user_profile(user_id: str) -> BaseUser:
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for user_id: {user_id}",
            )
        data = doc.to_dict()
        return BaseUser(id=user_id, **data)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {err}",
        )


def get_current_user(required_role: Optional[str] = None):
    async def _get_current_user(
        res: Response, credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
    ):
        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer authentication is needed",
                headers={'WWW-Authenticate': 'Bearer realm="auth_required"'},
            )
        try:
            decoded_token = auth.verify_id_token(credential.credentials)
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication from Firebase. {err}",
                headers={'WWW-Authenticate': 'Bearer error="invalid_token"'},
            )

        res.headers['WWW-Authenticate'] = 'Bearer realm="auth_required"'

        user_role = decoded_token.get('role')
        user_id = decoded_token.get('uid')

        user_profile = fetch_user_profile(user_id)

        # Check role hierarchy
        if required_role:
            user_role_level = ROLE_HIERARCHY.get(user_role, 0)
            required_role_level = ROLE_HIERARCHY.get(required_role, 0)
            if user_role_level < required_role_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User does not have the required role: {required_role}",
                )

        # return user_id
        return user_profile

    return _get_current_user


# Wrapper for current user with no role
def get_current_user_no_role():
    return get_current_user(required_role=None)


# Wrapper for current user with a specific role
def get_current_user_with_role(required_role: str):
    return get_current_user(required_role=required_role)
