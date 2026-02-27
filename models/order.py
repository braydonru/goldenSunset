from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from .producto import Product
from .user import User
import os

class Order(SQLModel, table=True):
    id:int = Field(primary_key=True)
    user:int = Field(foreign_key='user.id')

    size:Optional[str] = Field(default=None)
    color:Optional[str] = Field(default=None)
    type:Optional[str] = Field(default=None)
    specification:Optional[str] = Field(default=None)
    font:Optional[str] = Field(default=None)

    client_img:Optional[str] = Field(default=None)
    preview_img:Optional[str] = Field(default=None)

    client_img_back: Optional[str] = Field(default=None)
    preview_img_back: Optional[str] = Field(default=None)

    variation:Optional[str]= Field(default=None)

    date:datetime = Field(default_factory=datetime.now)

    def delete_images(self, static_dir: str = "static"):

        image_fields = [
            self.client_img,
            self.preview_img,
            self.client_img_back,
            self.preview_img_back
        ]

        for image_url in image_fields:
            if image_url:
                physical_path = self._url_to_physical_path(image_url, static_dir)

                if physical_path and os.path.exists(physical_path):
                    try:
                        os.remove(physical_path)
                    except Exception as e:
                        print(f"❌ Error al eliminar {physical_path}: {e}")
                else:
                    print(f"⚠️ Archivo no encontrado: {physical_path}")

    def _url_to_physical_path(self, image_url: str, static_dir: str) -> Optional[str]:

        if not image_url:
            return None


        if image_url.startswith('/static/'):
            relative_path = image_url.replace('/static/', '', 1)
        else:
            relative_path = image_url


        physical_path = os.path.join(static_dir, relative_path)

        return physical_path


class OrderCreateIn(SQLModel):
    user:str = Field(foreign_key='user.email')

    size:Optional[str] = Field(default=None)
    color:Optional[str] = Field(default=None)
    type:Optional[str] = Field(default=None)

    client_img:Optional[str] = Field(default=None)
    preview_img:Optional[str] = Field(default=None)


