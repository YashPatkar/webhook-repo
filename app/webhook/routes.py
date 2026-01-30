from flask import Blueprint, request, render_template   
from app.extensions import mongo
from datetime import datetime

webhook = Blueprint("Webhook", __name__, url_prefix="/webhook")

@webhook.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@webhook.route("/receiver", methods=["POST"])
def receiver():
    '''Webhook for github'''
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json

    doc = None

    # TRIGGERS ON PUSH
    if event_type == "push":
        doc = {
            "request_id": payload["head_commit"]["id"],
            "author": payload["pusher"]["name"],
            "action": "PUSH",
            "from_branch": None,
            "to_branch": payload["ref"].split("/")[-1],
            "timestamp": datetime.fromisoformat(
                payload["head_commit"]["timestamp"].replace("Z", "+00:00")
            )
        }

    # TRIGGERS ON PULL AND MERGE
    elif event_type == "pull_request":
        action = payload.get("action")
        pr = payload["pull_request"]

        # TRIGGERS ON MERGE
        if action == "closed" and pr.get("merged") is True:
            doc = {
                "request_id": pr["id"],
                "author": pr["user"]["login"],
                "action": "MERGE",
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": datetime.fromisoformat(
                    pr["merged_at"].replace("Z", "+00:00")
                )
            }

        # TRIGGERS ON PULL
        else:
            doc = {
                "request_id": pr["id"],
                "author": pr["user"]["login"],
                "action": "PULL_REQUEST",
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": datetime.fromisoformat(
                    pr["created_at"].replace("Z", "+00:00")
                )
            }

    if doc:
        # INSERT INTO MONGODB
        mongo.db.events.insert_one(doc)

    return {}, 200


@webhook.route("/events", methods=["GET"])
def get_events():
    '''Get all the events'''
    events = mongo.db.events.find().sort("timestamp", -1)

    result = []
    for event in events:
        event["_id"] = str(event["_id"])
        
        if isinstance(event["timestamp"], datetime):
            event["timestamp"] = event["timestamp"].isoformat()
            
        result.append(event)

    return {"events": result}, 200