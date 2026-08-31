# Project: Team Issue Tracker API

### Purpose

Build a backend API for a small team to manage **projects, issues, users, and issue discussions**.

Imagine a company has several software projects. Team members can create issues, assign them to other members, change their status and priority, leave comments, and track what is happening.

The API should support different levels of access depending on who is using it.

The important part: **you decide the internal architecture and implementation yourself.** The requirements below describe what the system must *do*, not how you should build it.

---

# Core Requirements

## 1. Users

The system needs users with:

* Name
* Email
* Password
* Role

There should be at least three roles:

* **Admin** — manages users and projects
* **Manager** — manages projects and issues
* **Member** — works with issues assigned to them

Users should be able to:

* Register
* Log in
* View their own profile
* Update their profile
* Change their password

Admins should be able to:

* View users
* Create users
* Update users
* Disable users

Disabled users should no longer be able to use the system.

---

# 2. Projects

A project represents something the team is working on.

Each project has:

* Name
* Description
* Status
* Creation date
* Owner
* Team members

Project statuses could include:

* Active
* Completed
* Archived

Users should be able to:

* View projects they belong to
* View project details
* Create projects
* Update projects
* Archive projects
* Add/remove team members

Not every user should be allowed to perform every action.

---

# 3. Issues

An issue belongs to a project.

Each issue has:

* Title
* Description
* Status
* Priority
* Creator
* Assignee
* Creation date
* Last update date
* Due date

Issue statuses:

* Open
* In Progress
* Resolved
* Closed

Priorities:

* Low
* Medium
* High
* Critical

Users should be able to:

* Create issues
* View issues
* Update issues
* Assign issues
* Change their status
* Change their priority
* Delete issues

But permissions should depend on the user's role and relationship to the project.

For example, a regular member shouldn't automatically have the same powers as a manager.

---

# 4. Comments

Users should be able to discuss an issue through comments.

A comment has:

* Author
* Content
* Creation date
* Last update date

Users should be able to:

* Add comments
* View comments
* Edit their own comments
* Delete their own comments

Administrators/managers may have broader permissions.

---

# 5. Filtering & Searching

The issue list should support things like:

* Search by title
* Filter by status
* Filter by priority
* Filter by assignee
* Filter by creator
* Filter by project
* Filter by due date
* Pagination
* Sorting

For example, someone should be able to ask:

> Give me the first 20 high-priority issues assigned to John that are currently in progress.

---

# 6. Project Dashboard

A project should have some basic statistics.

For example:

* Total issues
* Open issues
* In-progress issues
* Resolved issues
* Closed issues
* Critical issues
* Issues assigned to each team member

The API should provide this information through a dedicated endpoint.

---

# 7. Activity History

Important actions should be recorded.

For example:

> Kanan assigned Issue #42 to Alice.

> Alice changed Issue #42 from `Open` to `In Progress`.

> Bob changed the priority from `Medium` to `High`.

> Admin disabled Alice's account.

Users with appropriate permissions should be able to view the activity history of a project or issue.

---

# 8. Validation & Error Handling

The API should properly handle things such as:

* Invalid input
* Missing required data
* Non-existent users/projects/issues
* Duplicate emails
* Invalid status transitions
* Unauthorized actions
* Access to projects the user doesn't belong to
* Assigning an issue to someone who isn't part of the project

Errors should be consistent and understandable.

---

# 9. Authentication & Authorization

The API must distinguish between:

**Who are you?**

and

**Are you allowed to do this?**

Users must authenticate before accessing protected functionality.

Different roles should have different permissions.

For example:

| Action                        | Admin | Manager |    Member   |
| ----------------------------- | :---: | :-----: | :---------: |
| Manage users                  |   ✅   |    ❌    |      ❌      |
| Create project                |   ✅   |    ✅    |      ❌      |
| Manage project members        |   ✅   |    ✅    |      ❌      |
| Create issue                  |   ✅   |    ✅    |      ✅      |
| Assign issue                  |   ✅   |    ✅    |   Limited   |
| Edit own comment              |   ✅   |    ✅    |      ✅      |
| Delete another user's comment |   ✅   |    ✅    |      ❌      |
| View project                  |   ✅   |    ✅    | Member only |

You can refine the exact permission model yourself.

---

# 10. API Documentation

The API should be understandable by another developer who has never seen your code.

Someone should be able to:

1. Start the application.
2. Open the API documentation.
3. Understand the available endpoints.
4. Authenticate.
5. Create a project.
6. Add team members.
7. Create issues.
8. Work with those issues.

---

# What makes this **mid-level**

This isn't difficult because there are 50 endpoints.

It's difficult because several concepts interact:

**authentication → authorization → users → projects → membership → issues → comments → filtering → database relationships → validation → business rules**

You'll have to make decisions about things like:

* Where business rules belong
* How to structure the application
* How authentication flows through requests
* How permissions are checked
* How database relationships work
* How updates should behave
* How filtering/searching should be designed
* How to avoid putting everything inside route handlers
* How to handle transactions
* How to keep errors consistent

And that's exactly the kind of stuff I'd expect a **mid-level FastAPI developer** to be comfortable reasoning about.

### Suggested constraint

Don't follow a tutorial for this one.

Use the **FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Alembic, JWT/authentication, Docker, and pytest** ecosystem you've been studying, but don't look up a project implementation.

Docs are fair game. AI is fair game for **understanding a library/API or debugging something you've tried**. But don't ask AI to architect the whole application for you.

The real test is:

> **Can you take a set of business requirements and turn them into a working backend without someone handing you the architecture?**

