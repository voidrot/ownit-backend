# OwnIt Backend

The OwnIt backend powers a family-focused app for assigning and completing chores and tracking progress over time.

## Core concepts (high level)

- **Chores**: Definitions of recurring or one-off work, optionally with instructions/media.
- **Assignments**: A chore assigned to a specific user with a due date and completion state.
- **Evidence**: Optional photos/videos attached to an assignment as proof of completion.
- **Points**: A scoring mechanism associated with chores (and optional penalties).


## TODO

- [ ] Enhance chore model to use a many-to-many instruction video model so that multiple instructional videos can be added to a chore