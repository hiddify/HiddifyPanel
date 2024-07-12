from apiflask import Schema, fields
# region info


class PanelInfoOutputSchema(Schema):
    version = fields.String(description="The panel version")
# endregion


class PongOutputSchema(Schema):
    msg = fields.String(description="Pong Response")
# endregion
