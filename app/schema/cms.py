from typing import List, Optional
from pydantic import BaseModel

class NavbarLinkSchema(BaseModel):
    label: str
    url: str
    id: str

class NavbarSchema(BaseModel):
    id: Optional[int] = None
    logo_url: str
    brand_name: Optional[str] = None
    links: Optional[List[dict]] = None

class HeroSchema(BaseModel):
    id: Optional[int] = None
    title: str
    subtitle: str
    button_text: str
    background_image_url: str

class NavbarUpdateSchema(BaseModel):
    logo_url: Optional[str] = None
    brand_name: Optional[str] = None
    links: Optional[List[dict]] = None

class HeroUpdateSchema(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    button_text: Optional[str] = None
    background_image_url: Optional[str] = None

class ProgramSectionSchema(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    button_text: str
    background_image_url: str
    card1_title: str
    card1_image_url: str
    card2_title: str
    card2_image_url: str

class ProgramSectionUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    button_text: Optional[str] = None
    background_image_url: Optional[str] = None
    card1_title: Optional[str] = None
    card1_image_url: Optional[str] = None
    card2_title: Optional[str] = None
    card2_image_url: Optional[str] = None

class EventSchema(BaseModel):
    id: Optional[int] = None
    title: str
    date_text: str
    image_url: str
    button_text: str
    order: int = 0

class EventUpdateSchema(BaseModel):
    title: Optional[str] = None
    date_text: Optional[str] = None
    image_url: Optional[str] = None
    button_text: Optional[str] = None
    order: Optional[int] = None

class EnlightenmentSchema(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    video_url: str
    background_image_url: str
    founder_name: str
    founder_role: str

class EnlightenmentUpdateSchema(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    background_image_url: Optional[str] = None
    founder_name: Optional[str] = None
    founder_role: Optional[str] = None

class TestimonialSchema(BaseModel):
    id: Optional[int] = None
    author_name: str
    author_role: str
    quote: str
    order: int = 0

class TestimonialUpdateSchema(BaseModel):
    author_name: Optional[str] = None
    author_role: Optional[str] = None
    quote: Optional[str] = None
    order: Optional[int] = None

class ContactInfoSchema(BaseModel):
    id: Optional[int] = None
    title: str
    subtitle: str
    email: str
    support_text: str
    location: str
    phone: str
    website: str
    background_image_url: str
    form_background_image_url: str

class ContactInfoUpdateSchema(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    email: Optional[str] = None
    support_text: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    background_image_url: Optional[str] = None
    form_background_image_url: Optional[str] = None

class FooterInfoSchema(BaseModel):
    id: Optional[int] = None
    newsletter_title: str
    newsletter_description: str
    facebook_url: str
    instagram_url: str
    twitter_url: str
    mail_url: str
    logo_url: str
    copyright_text: str
    background_image_url: str

class FooterInfoUpdateSchema(BaseModel):
    newsletter_title: Optional[str] = None
    newsletter_description: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    mail_url: Optional[str] = None
    logo_url: Optional[str] = None
    copyright_text: Optional[str] = None
    background_image_url: Optional[str] = None

class CMSPageSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CMSPageCreate(BaseModel):
    name: str

class CMSPageUpdate(BaseModel):
    name: str

class SectionSchema(BaseModel):
    id: Optional[int] = None
    page_id: Optional[int] = None
    section_id: str
    template_id: str = "default"
    content: dict

class SectionListSchema(BaseModel):
    id: int
    page_id: Optional[int] = None
    section_id: str
    template_id: str

class SectionCreate(BaseModel):
    page_id: Optional[int] = None
    section_id: str
    template_id: str = "default"
    content: dict

class SectionUpdate(BaseModel):
    page_id: Optional[int] = None
    template_id: Optional[str] = None
    content: Optional[dict] = None
