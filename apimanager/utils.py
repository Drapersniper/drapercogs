from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_id: str
    is_blacklisted: bool = False
    is_superuser: bool = False
    is_admin: bool = False
    is_mod: bool = False
    is_contributor: bool = False
    is_user: bool = False
    is_guest: bool = False
    name: str = "Unauthenticated"
    entries_submitted: int = 0
    token: Optional[str] = None
    updated_on: str = None
    blacklisted_on: str = None
    registered_on: str = None
    md5: str = None
    id: int = None
    can_delete: bool = False
    can_post: bool = False
    can_read: bool = False

    def __post_init__(self):
        self.is_blacklisted = bool(int(self.is_blacklisted))
        self.is_superuser = bool(int(self.is_superuser))
        self.is_admin = bool(int(self.is_admin))
        self.is_mod = bool(int(self.is_mod))
        self.is_contributor = bool(int(self.is_contributor))
        self.is_user = bool(int(self.is_user))
        self.is_guest = bool(int(self.is_guest))
        if not self.name:
            self.name = "Unauthenticated"
        else:
            if type(self.name) is bytes:
                self.name = self.name.decode()
        if not self.token:
            self.token = None
        else:
            if type(self.token) is bytes:
                self.token = self.token.decode()
        self.user_id = str(self.user_id)
        self.entries_submitted = int(self.entries_submitted)
        self.can_read = not self.is_blacklisted and any(
            [
                self.is_user,
                self.is_contributor,
                self.is_mod,
                self.is_admin,
                self.is_superuser,
            ]
        )
        self.can_post = self.can_read and not self.is_user
        self.can_delete = self.can_post and not self.is_contributor

    def to_json(self):
        return dict(
            user_id=self.user_id,
            entries_submitted=self.entries_submitted,
            is_guest=self.is_guest,
            is_user=self.is_user,
            is_contributor=self.is_contributor,
            is_mod=self.is_mod,
            is_admin=self.is_admin,
            is_superuser=self.is_superuser,
            is_blacklisted=self.is_blacklisted,
            name=self.name,
        )

    def to_json_full(self):
        return dict(
            user_id=self.user_id,
            entries_submitted=self.entries_submitted,
            is_guest=self.is_guest,
            is_user=self.is_user,
            is_contributor=self.is_contributor,
            is_mod=self.is_mod,
            is_admin=self.is_admin,
            is_superuser=self.is_superuser,
            is_blacklisted=self.is_blacklisted,
            name=self.name,
            token=self.token,
        )
