# Get Task

> Get detailed information about a specific AI agent task.

Retrieves comprehensive information about a task, including its current status,
progress, and detailed execution data. You can choose to get just the status
(for quick polling) or full details including steps and file information.

Use this endpoint to:

- Monitor task progress in real-time
- Review completed task results
- Debug failed tasks by examining steps
- Download output files and logs

Args:

- task_id: The unique identifier of the agent task

Returns:

- Complete task information

Raises:

- 404: If the user agent task doesn't exist

## OpenAPI

```yaml https://app.stainless.com/api/spec/documented/browser-use/openapi.documented.yml get /tasks/{task_id}
paths:
  path: /tasks/{task_id}
  method: get
  request:
    security:
      - title: APIKeyHeader
        parameters:
          query: {}
          header:
            X-Browser-Use-API-Key:
              type: apiKey
          cookie: {}
    parameters:
      path:
        task_id:
          schema:
            - type: string
              required: true
              title: Task Id
              format: uuid
      query: {}
      header: {}
      cookie: {}
    body: {}
    codeSamples:
      - lang: JavaScript
        source: >-
          import BrowserUse from 'browser-use-sdk';


          const client = new BrowserUse({
            apiKey: 'My API Key',
          });


          const taskView = await
          client.tasks.retrieve('182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e');


          console.log(taskView.id);
      - lang: Python
        source: |-
          from browser_use_sdk import BrowserUse

          client = BrowserUse(
              api_key="My API Key",
          )
          task_view = client.tasks.retrieve(
              "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
          )
          print(task_view.id)
  response:
    "200":
      application/json:
        schemaArray:
          - type: object
            properties:
              id:
                allOf:
                  - type: string
                    format: uuid
                    title: Id
              sessionId:
                allOf:
                  - type: string
                    format: uuid
                    title: Sessionid
              session:
                allOf:
                  - $ref: "#/components/schemas/TaskSessionView"
              llm:
                allOf:
                  - type: string
                    title: Llm
              task:
                allOf:
                  - type: string
                    title: Task
              status:
                allOf:
                  - $ref: "#/components/schemas/TaskStatus"
              startedAt:
                allOf:
                  - type: string
                    format: date-time
                    title: Startedat
              finishedAt:
                allOf:
                  - anyOf:
                      - type: string
                        format: date-time
                      - type: "null"
                    title: Finishedat
              metadata:
                allOf:
                  - additionalProperties: true
                    type: object
                    title: Metadata
                    default: {}
              isScheduled:
                allOf:
                  - type: boolean
                    title: Isscheduled
              steps:
                allOf:
                  - items:
                      $ref: "#/components/schemas/TaskStepView"
                    type: array
                    title: Steps
              doneOutput:
                allOf:
                  - anyOf:
                      - type: string
                      - type: "null"
                    title: Doneoutput
              userUploadedFiles:
                allOf:
                  - items:
                      $ref: "#/components/schemas/FileView"
                    type: array
                    title: Useruploadedfiles
              outputFiles:
                allOf:
                  - items:
                      $ref: "#/components/schemas/FileView"
                    type: array
                    title: Outputfiles
              browserUseVersion:
                allOf:
                  - anyOf:
                      - type: string
                      - type: "null"
                    title: Browseruseversion
              isSuccess:
                allOf:
                  - anyOf:
                      - type: boolean
                      - type: "null"
                    title: Issuccess
            title: TaskView
            description: |-
              View model for representing a task with its execution details

              Attributes:
                  id: Unique identifier for the task
                  session_id: ID of the session this task belongs to
                      session: The session this task belongs to
                  llm: The LLM model used for this task represented as a string
                  task: The task prompt/instruction given to the agent
                  status: Current status of the task execution
                  started_at: Naive UTC timestamp when the task was started
                  finished_at: Naive UTC timestamp when the task completed (None if still running)
                  metadata: Optional additional metadata associated with the task set by the user
                  is_scheduled: Whether this task was created as a scheduled task
                  steps: List of execution steps
                  done_output: Final output/result of the task
                  user_uploaded_files: List of files uploaded by user for this task
                  output_files: List of files generated as output by this task
                  browser_use_version: Version of browser-use used for this task (older tasks may not have this set)
                      is_success: Whether the task was successful (self-reported by the agent)
            refIdentifier: "#/components/schemas/TaskView"
            requiredProperties:
              - id
              - sessionId
              - session
              - llm
              - task
              - status
              - startedAt
              - isScheduled
              - steps
              - userUploadedFiles
              - outputFiles
        examples:
          example:
            value:
              id: 3c90c3cc-0d44-4b50-8888-8dd25736052a
              sessionId: 3c90c3cc-0d44-4b50-8888-8dd25736052a
              session:
                id: 3c90c3cc-0d44-4b50-8888-8dd25736052a
                status: active
                liveUrl: <string>
                startedAt: "2023-11-07T05:31:56Z"
                finishedAt: "2023-11-07T05:31:56Z"
              llm: <string>
              task: <string>
              status: started
              startedAt: "2023-11-07T05:31:56Z"
              finishedAt: "2023-11-07T05:31:56Z"
              metadata: {}
              isScheduled: true
              steps:
                - number: 123
                  memory: <string>
                  evaluationPreviousGoal: <string>
                  nextGoal: <string>
                  url: <string>
                  screenshotUrl: <string>
                  actions:
                    - <string>
              doneOutput: <string>
              userUploadedFiles:
                - id: 3c90c3cc-0d44-4b50-8888-8dd25736052a
                  fileName: <string>
              outputFiles:
                - id: 3c90c3cc-0d44-4b50-8888-8dd25736052a
                  fileName: <string>
              browserUseVersion: <string>
              isSuccess: true
        description: Successful Response
    "422":
      application/json:
        schemaArray:
          - type: object
            properties:
              detail:
                allOf:
                  - items:
                      $ref: "#/components/schemas/ValidationError"
                    type: array
                    title: Detail
            title: HTTPValidationError
            refIdentifier: "#/components/schemas/HTTPValidationError"
        examples:
          example:
            value:
              detail:
                - loc:
                    - <string>
                  msg: <string>
                  type: <string>
        description: Validation Error
  deprecated: false
  type: path
components:
  schemas:
    FileView:
      properties:
        id:
          type: string
          format: uuid
          title: Id
        fileName:
          type: string
          title: Filename
      type: object
      required:
        - id
        - fileName
      title: FileView
      description: |-
        View model for representing an output file generated by the agent

        Attributes:
                id: Unique identifier for the output file
                file_name: Name of the output file
    TaskSessionStatus:
      type: string
      enum:
        - active
        - stopped
      title: TaskSessionStatus
      description: |-
        Enumeration of possible (browser) session states

        Attributes:
            ACTIVE: Session is currently active and running (browser is running)
            STOPPED: Session has been stopped and is no longer active (browser is stopped)
    TaskSessionView:
      properties:
        id:
          type: string
          format: uuid
          title: Id
        status:
          $ref: "#/components/schemas/TaskSessionStatus"
        liveUrl:
          anyOf:
            - type: string
            - type: "null"
          title: Liveurl
        startedAt:
          type: string
          format: date-time
          title: Startedat
        finishedAt:
          anyOf:
            - type: string
              format: date-time
            - type: "null"
          title: Finishedat
      type: object
      required:
        - id
        - status
        - startedAt
      title: TaskSessionView
      description: |-
        View model for representing a session that a task belongs to

        Attributes:
                id: Unique identifier for the session
                status: Current status of the session (active/stopped)
                live_url: URL where the browser can be viewed live in real-time.
                started_at: Timestamp when the session was created and started.
                finished_at: Timestamp when the session was stopped (None if still active).
    TaskStatus:
      type: string
      enum:
        - started
        - paused
        - finished
        - stopped
      title: TaskStatus
      description: |-
        Enumeration of possible task execution states

        Attributes:
            STARTED: Task has been started and is currently running.
            PAUSED: Task execution has been temporarily paused (can be resumed)
            FINISHED: Task has finished and the agent has completed the task.
            STOPPED: Task execution has been manually stopped (cannot be resumed).
    TaskStepView:
      properties:
        number:
          type: integer
          title: Number
        memory:
          type: string
          title: Memory
        evaluationPreviousGoal:
          type: string
          title: Evaluationpreviousgoal
        nextGoal:
          type: string
          title: Nextgoal
        url:
          type: string
          title: Url
        screenshotUrl:
          anyOf:
            - type: string
            - type: "null"
          title: Screenshoturl
        actions:
          items:
            type: string
          type: array
          title: Actions
      type: object
      required:
        - number
        - memory
        - evaluationPreviousGoal
        - nextGoal
        - url
        - actions
      title: TaskStepView
      description: |-
        View model for representing a single step in a task's execution

        Attributes:
            number: Sequential step number within the task
            memory: Agent's memory at this step
            evaluation_previous_goal: Agent's evaluation of the previous goal completion
            next_goal: The goal for the next step
            url: Current URL the browser is on for this step
            screenshot_url: Optional URL to the screenshot taken at this step
            actions: List of stringified json actions performed by the agent in this step
    ValidationError:
      properties:
        loc:
          items:
            anyOf:
              - type: string
              - type: integer
          type: array
          title: Location
        msg:
          type: string
          title: Message
        type:
          type: string
          title: Error Type
      type: object
      required:
        - loc
        - msg
        - type
      title: ValidationError
```
