import sqlalchemy as sa

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("email", sa.Text, nullable=False, unique=True),
    sa.Column("password_hash", sa.Text, nullable=False),
    sa.Column(
        "created_at",
        sa.Text,
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    ),
)

user_profiles = sa.Table(
    "user_profiles",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "user_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    sa.Column("full_name", sa.Text),
    sa.Column("monthly_income", sa.Float, server_default=sa.text("0")),
    sa.Column("monthly_expenses", sa.Float, server_default=sa.text("0")),
    sa.Column("total_savings", sa.Float, server_default=sa.text("0")),
    sa.Column("emergency_fund", sa.Float, server_default=sa.text("0")),
    sa.Column("liabilities", sa.Float, server_default=sa.text("0")),
    sa.Column("existing_investments", sa.Float, server_default=sa.text("0")),
    sa.Column("created_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.Column("updated_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
)

goals = sa.Table(
    "goals",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "user_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("name", sa.Text, nullable=False),
    sa.Column("goal_type", sa.Text, nullable=False),
    sa.Column("target_amount", sa.Float, nullable=False),
    sa.Column("current_amount", sa.Float, server_default=sa.text("0")),
    sa.Column("monthly_contribution", sa.Float, server_default=sa.text("0")),
    sa.Column("horizon_years", sa.Float, nullable=False),
    sa.Column("description", sa.Text),
    sa.Column("status", sa.Text, server_default=sa.text("'active'")),
    sa.Column("created_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.Column("updated_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
)

risk_profiles = sa.Table(
    "risk_profiles",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "user_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("score", sa.Float, nullable=False),
    sa.Column("category", sa.Text, nullable=False),
    sa.Column("answers_json", sa.Text),
    sa.Column("created_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
)

analyses = sa.Table(
    "analyses",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "user_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "goal_id",
        sa.Integer,
        sa.ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("status", sa.Text, server_default=sa.text("'pending'")),
    sa.Column("final_response", sa.Text),
    sa.Column("validation_status", sa.Text),
    sa.Column("created_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.Column("completed_at", sa.Text),
)

portfolios = sa.Table(
    "portfolios",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "analysis_id",
        sa.Integer,
        sa.ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("strategy_name", sa.Text),
    sa.Column("allocation_json", sa.Text),
    sa.Column("expected_return", sa.Float),
    sa.Column("risk_level", sa.Text),
    sa.Column("created_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
)

scenarios = sa.Table(
    "scenarios",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "analysis_id",
        sa.Integer,
        sa.ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("scenario_name", sa.Text, nullable=False),
    sa.Column("projected_value", sa.Float),
    sa.Column("assumed_return", sa.Float),
    sa.Column("assumptions_json", sa.Text),
    sa.Column("created_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
)

agent_logs = sa.Table(
    "agent_logs",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "analysis_id",
        sa.Integer,
        sa.ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("agent_name", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("input_summary", sa.Text),
    sa.Column("output_summary", sa.Text),
    sa.Column("error_message", sa.Text),
    sa.Column("created_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
)

revoked_tokens = sa.Table(
    "revoked_tokens",
    metadata,
    sa.Column("token_id", sa.Text, primary_key=True),
    sa.Column("expires_at", sa.Integer, nullable=False),
    sa.Column("created_at", sa.Text, server_default=sa.text("CURRENT_TIMESTAMP")),
)
