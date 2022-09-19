import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from jira_client import JiraClient, JiraError
from settings import show_settings_dialog, validate_settings
from dataclasses import dataclass
from typing import List, Tuple, Any

import json
import apsync
import anchorpoint

aps = apsync.Api.instance()
ui = anchorpoint.UI()
ctx = anchorpoint.Context.instance()    

settings = apsync.Settings(
    identifier="jira"
)

PROJECT_KEY = settings.get("jira_project_key")
OUT_DIR = settings.get("local_folder")

JIRA = JiraClient(
    url=settings.get("jira_url"),
    email=settings.get("jira_email"),
    token=settings.get("jira_token"),
)

new_projects = 0
new_tasks = 0


@dataclass
class JiraStatus:
    id: str = ""
    name: str = ""
    color: str = ""


@dataclass
class JiraProject:
    id: str = ""
    key: str = ""
    name: str = ""


@dataclass
class JiraTask:
    id: str = ""
    key: str = ""
    name: str = ""
    assignee: str = ""
    status: str = ""


def map_status_color(c: str):
    if c == "red":
        return apsync.TagColor.red
    elif c == "green":
        return apsync.TagColor.green
    elif c == "blue":
        return apsync.TagColor.blue
    elif c == "blue-grey":
        return apsync.TagColor.grey
    elif c == "yellow":
        return apsync.TagColor.yellow


def get_jira_statuses():
    results = []

    root_project = JIRA.get_project(PROJECT_KEY)
    statuses = JIRA.get_statuses()

    for status in statuses:
        if "scope" in status and  \
                status["scope"]["type"] == "PROJECT" and \
                status["scope"]["project"]["id"] == root_project["id"]:
            results.append(JiraStatus(
                id=status["id"],
                name=status["name"],
                color=status["statusCategory"]["colorName"]
            ))
    
    return results


def get_jira_projects():
    results = []

    issues = JIRA.search_issues(
        jql=f"project = {PROJECT_KEY} AND issuetype = Epic",
        fields=["issuelinks", "summary"]
    )

    for issue in issues:
        issuelinks = issue["fields"]["issuelinks"]
        if len(issuelinks) != 1:
            continue

        prefix = issuelinks[0]["inwardIssue"]["key"]
        summary = issue["fields"]["summary"]

        results.append(JiraProject(
            id=issue["id"],
            key=issue["key"],
            name=f"{prefix}-{summary}"
        ))

    return results


def get_jira_tasks(project: JiraProject) -> List[JiraTask]:
    tasks = []

    issues = JIRA.search_issues(
        jql=f"project = {PROJECT_KEY} AND issuetype = Task AND parent = {project.key}",
        fields=["assignee", "status", "summary"]
    )

    for issue in issues:
        assignee = issue["fields"]["assignee"]
        assignee = assignee["emailAddress"] if assignee != None else ""

        status = issue["fields"]["status"]["name"]

        tasks.append(JiraTask(
            id=issue["id"],
            key=issue["key"],
            name=issue["fields"]["summary"],
            assignee=assignee,
            status=status
        ))

    return tasks


def sync_projects():
    jira_projects = get_jira_projects()

    for p in jira_projects:
        sync_project(p)


def sync_project(p: JiraProject):
    global new_projects

    project_root = os.path.join(OUT_DIR, p.name)

    if not os.path.isdir(project_root):
        os.makedirs(project_root, exist_ok=True)
    
    if not apsync.is_project(project_root):        
        ap_proj = ctx.create_project(project_root, p.name)
        new_projects += 1
    else:
        ap_proj = apsync.get_project(project_root)

    sync_tasks(ap_proj, p, project_root)


def sync_tasks(ap_proj: apsync.Project, jira_proj: JiraProject, project_root: str):
    jira_tasks = get_jira_tasks(jira_proj)

    for t in jira_tasks:
        sync_task(ap_proj, jira_proj, t, project_root)


def sync_task(ap_proj: apsync.Project, p: JiraProject, t: JiraTask, project_root: str):
    global new_tasks

    task_root = os.path.join(project_root, t.name)

    if not os.path.isdir(task_root):
        os.makedirs(task_root, exist_ok=True)
        new_tasks += 1

    # Add members
    proj_members = [m.email for m in apsync.get_project_members(ap_proj.workspace_id, ap_proj.id)]
    if t.assignee != "" and not t.assignee in proj_members:
        apsync.add_user_to_project(
            ap_proj.workspace_id,
            ap_proj.id,
            "Jira",
            t.assignee,
            apsync.AccessLevel.Member
        )

    # Create new tags
    statuses = get_jira_statuses()
    for status in statuses:
        apsync.set_attribute_tag(task_root, "Status", status.name,
            auto_create=True,
            tag_color=map_status_color(status.color)
        )

    # Set current tag
    apsync.set_attribute_tag(task_root, "Status", t.status)


# Main
def main():
    global new_projects
    global new_tasks

    try:
        sync_projects()
        msgs = []

        if new_projects > 0:
            msgs.append(f"New projects: {new_projects}")
        if new_tasks > 0:
            msgs.append(f"New tasks: {new_tasks}")

        ui.show_success("Jira sync successful", "\n".join(msgs), 6000)

    except JiraError as e:
        ui.show_error("Jira sync failed", f"{e}")



if __name__ == "__main__":
    if len(validate_settings()) == 0:
        ctx.run_async(main)
    else:
        ui.show_info("Jira setup incomplete, opening settings ...")
        show_settings_dialog()


def on_attributes_changed(parent_path: str, attributes: List[anchorpoint.AttributeChange], ctx: anchorpoint.Context):
    print("Attribute changed")