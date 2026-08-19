from pydantic import BaseModel, Field, StrictInt, field_validator


class ImportRequest(BaseModel):
    username: str | None = None
    months: int = 3


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    ply: int = 0
    history: list[ChatMessage] = Field(default_factory=list)


class SettingsUpdate(BaseModel):
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    chesscom_username: str | None = None
    claude_model: str | None = None
    gemini_model: str | None = None
    gemini_fallback_models: str | None = None
    engine_movetime_ms: int | None = None
    engine_multipv: int | None = None
    engine_threads: int | None = None
    stockfish_path: str | None = None
    coach_provider: str | None = None
    ollama_url: str | None = None
    ollama_model: str | None = None


class BotAdvancedSettings(BaseModel):
    label: str | None = None
    skill_level: StrictInt | None = Field(default=None, ge=0, le=20)
    move_time_ms: StrictInt | None = Field(default=None, ge=10, le=5000)
    randomness: float | None = Field(default=None, ge=0, le=1)

    @field_validator("randomness", mode="before")
    @classmethod
    def validate_randomness_type(cls, value):
        if value is None:
            return value
        if type(value) not in {int, float}:
            raise ValueError("randomness must be a number")
        return value


class BotGameCreate(BaseModel):
    player_color: str = "white"
    difficulty: str = "club"
    advanced: BotAdvancedSettings | None = None


class BotMoveRequest(BaseModel):
    from_square: str = Field(alias="from")
    to: str
    promotion: str | None = None
