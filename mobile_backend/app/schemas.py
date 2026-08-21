from pydantic import BaseModel, Field


class SendSingleRequest(BaseModel):
    user_id: str = Field(min_length=1)
    recipient: str = Field(min_length=3)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)


class SendBatchRequest(BaseModel):
    user_id: str = Field(min_length=1)
    recipient: str = Field(min_length=3)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    count: int = Field(ge=1, le=500)
    min_delay_seconds: float = Field(default=5.0, ge=0.0)
    max_delay_seconds: float = Field(default=30.0, ge=0.0)


class SendResponse(BaseModel):
    sent: bool
    message: str


class BatchResponse(BaseModel):
    requested: int
    sent: int
    failed: int


class SubscriptionStartRequest(BaseModel):
    user_id: str = Field(min_length=1)
    plan: str = Field(min_length=1)
    phone_number: str = Field(min_length=9)


class SubscriptionStartResponse(BaseModel):
    merchant_request_id: str
    checkout_request_id: str
    response_code: str
    response_description: str
    customer_message: str
    amount: int


class SubscriptionStatusResponse(BaseModel):
    result_code: str
    result_desc: str
    checkout_request_id: str
    status: str


class SubscriptionVerificationResponse(BaseModel):
    has_active_subscription: bool
    message: str
    plan: str | None = None
    checkout_request_id: str | None = None
    status: str | None = None
    expires_at: str | None = None
    amount: int | None = None
