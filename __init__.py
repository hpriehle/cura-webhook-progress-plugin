from . import WebhookProgressPlugin

def getMetaData():
    return {}

def register(app):
    return {"extension": WebhookProgressPlugin.WebhookProgressPlugin()}
