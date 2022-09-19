# Jira

Python Jira Integration for Anchorpoint

## Getting started

Use the [Action Distribution](https://docs.anchorpoint.app/docs/5-Actions/2-Create-Actions/#distribution) in Anchorpoint to import the integration in Anchorpoint. Simply copy and paste the URL of this repository. Every teammember in your workspace will have access to this action automatically. You need a Jira account with an [API token](https://id.atlassian.com/manage-profile/security/api-tokens). 

## Sync Jira projects

The integration only synchronizes epics from a deposited project. These Epics are only synchronized as soon as another Epic from another project is linked as a "Linked issue". This way Anchorpoint can produce the correct naming convention from 2 linked Epics. So for a synchronization always 2 projects are needed.