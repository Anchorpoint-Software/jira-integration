from typing import List, Tuple, Any

import apsync
import anchorpoint


def on_save(dialog: anchorpoint.Dialog):
    dialog.store_settings()

    ui = anchorpoint.UI()
    if validate_settings():
        dialog.close()
    else:
        ui.show_error("The configuration is still incomplete", "Please fill in all fields to complete the configuration.")


def get_settings() -> apsync.Settings:
    return apsync.Settings(
        identifier="jira"
    )


def validate_settings() -> bool:
    settings = get_settings()

    if settings.get("local_folder", "") == "":
        return False
    if settings.get("jira_email", "") == "":
        return False
    if settings.get("jira_token", "") == "":
        return False
    if settings.get("jira_url", "") == "":
        return False
    if settings.get("jira_project_key", "") == "":
        return False

    return True


def show_settings_dialog():
    ctx = anchorpoint.Context.instance()
    ui = anchorpoint.UI()

    settings = get_settings()

    dialog = anchorpoint.Dialog()
    dialog.title = "Jira Synchronization Settings"

    dialog.add_text("Project Folder").add_input(
        default= '',
        placeholder='Z:\Projects',
        var="local_folder",
        browse=anchorpoint.BrowseType.Folder
    )
    dialog.add_info("This is the place in which Jira will create project folders based on Epics.")

    dialog.start_section(text="Jira Credentials", foldable=False, folded=False)

    dialog.add_text("Email \t") \
        .add_input(
            default= '',
            placeholder='john@anchorpoint.app',
            var="jira_email",
            width=316
        )

    dialog.add_text("Token \t") \
        .add_input(
            default= '',
            placeholder='',
            password=True,
            var="jira_token",
            width=316
        )

    dialog.add_info("You can create a token in your <a href='https://id.atlassian.com/manage-profile/security/api-tokens'>profile</a>")

    dialog.end_section()

    dialog.start_section(text="Jira Projects", foldable=False, folded=False)

    dialog.add_text("URL \t") \
        .add_input(
            default= '',
            placeholder="https://my-domain.atlassian.net",
            callback=None,
            var="jira_url",
            width=316
        )

    dialog.add_text("Project Key \t") \
        .add_input(
            default= '',
            placeholder="AI for Anchorpoint-Integration",
            callback=None,
            var="jira_project_key",
            width=316
        )

    dialog.add_info("This is the abbreviation of your project, which is placed e.g. in front of <br> each Task or Epic.")

    dialog.end_section()

    dialog.add_button(
        text="Apply",
        callback=on_save,
    )

    dialog.show(
        settings=settings,
        store_settings_on_close=False
    )


if __name__ == "__main__":
    show_settings_dialog()