from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, ForeignKeyConstraint, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from typing import Optional, List, Dict, Any
from webagent.models import ProviderEnum

engine = create_engine('sqlite:///tasks.db', echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    model = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    webhook_url = Column(String, nullable=True)
    response_format = Column(String, default='text')
    json_schema = Column(String, nullable=True)
    cached_workflow = Column(JSON, nullable=True)
    use_cached_workflow = Column(Boolean, default=False)
    runs = relationship("TaskRun", back_populates="task", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "prompt": self.prompt,
            "model": self.model,
            "provider": self.provider,
            "webhook_url": self.webhook_url,
            "response_format": self.response_format,
            "json_schema": self.json_schema,
            "cached_workflow": self.cached_workflow,
            "use_cached_workflow": self.use_cached_workflow
        }


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    model = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    webhook_url = Column(String, nullable=True)
    response_format = Column(String, default='text')
    json_schema = Column(String, nullable=True)
    result = Column(Text, nullable=True)
    is_done = Column(Boolean, default=False)
    is_successful = Column(Boolean, nullable=True)
    webhook_result_success = Column(Boolean, nullable=True)
    webhook_result_status_code = Column(Integer, nullable=True)
    webhook_result_message = Column(Text, nullable=True)
    task = relationship("Task", back_populates="runs")
    steps = relationship("RunStep", back_populates="task_run", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "prompt": self.prompt,
            "model": self.model,
            "provider": self.provider,
            "webhook_url": self.webhook_url,
            "response_format": self.response_format,
            "json_schema": self.json_schema,
            "result": self.result,
            "is_done": self.is_done,
            "is_successful": self.is_successful,
            "webhook_result_success": self.webhook_result_success,
            "webhook_result_status_code": self.webhook_result_status_code,
            "webhook_result_message": self.webhook_result_message,
            "steps": [step.to_dict() for step in self.steps]
        }


class RunStep(Base):
    __tablename__ = "run_steps"

    task_run_id = Column(Integer, ForeignKey("task_runs.id"), primary_key=True)
    step_number = Column(Integer, primary_key=True)
    description = Column(Text, nullable=True)
    screenshot = Column(Text, nullable=True)
    task_run = relationship("TaskRun", back_populates="steps")
    actions = relationship("RunAction", back_populates="run_step", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "task_run_id": self.task_run_id,
            "step_number": self.step_number,
            "description": self.description,
            "screenshot": self.screenshot,
            "actions": [action.to_dict() for action in self.actions]
        }


class RunAction(Base):
    __tablename__ = "run_actions"

    id = Column(Integer, primary_key=True, index=True)
    task_run_id = Column(Integer, nullable=False)
    step_number = Column(Integer, nullable=False)
    action_number = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    params = Column(JSON, nullable=True)
    is_done = Column(Boolean, default=False)
    success = Column(Boolean, nullable=True)
    extracted_content = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    include_in_memory = Column(Boolean, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ['task_run_id', 'step_number'],
            ['run_steps.task_run_id', 'run_steps.step_number']
        ),
    )

    run_step = relationship("RunStep", back_populates="actions")

    def to_dict(self):
        return {
            "id": self.id,
            "task_run_id": self.task_run_id,
            "step_number": self.step_number,
            "action_number": self.action_number,
            "name": self.name,
            "params": self.params,
            "is_done": self.is_done,
            "success": self.success,
            "extracted_content": self.extracted_content,
            "error": self.error,
            "include_in_memory": self.include_in_memory,
        }

Base.metadata.create_all(bind=engine)

def create_task(prompt: str, model: str, provider: str, webhook_url: Optional[str] = None, response_format: Optional[str] = 'text', json_schema: Optional[str] = None, cached_workflow: Optional[Dict[str, Any]] = None, use_cached_workflow: bool = False) -> Task:
    """Create a new task in the database"""
    db = SessionLocal()
    try:
        task = Task(prompt=prompt, model=model, provider=provider, webhook_url=webhook_url, response_format=response_format, json_schema=json_schema, cached_workflow=cached_workflow, use_cached_workflow=use_cached_workflow)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    finally:
        db.close()


def update_task(task_id: int, data: Dict[str, Any]) -> Optional[Task]:
    """Update an existing task in the database"""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        db.commit()
        db.refresh(task)
        return task
    finally:
        db.close()


def create_task_run(task_id: int, prompt: str, model: str, provider: str, webhook_url: Optional[str] = None, response_format: Optional[str] = 'text', json_schema: Optional[str] = None) -> TaskRun:
    """Create a new task run in the database"""
    db = SessionLocal()
    try:
        task_run = TaskRun(
            task_id=task_id,
            prompt=prompt,
            model=model,
            provider=provider,
            webhook_url=webhook_url,
            response_format=response_format,
            json_schema=json_schema,
            is_done=False
        )
        db.add(task_run)
        db.commit()
        db.refresh(task_run)
        return task_run
    finally:
        db.close()


def update_task_run(task_run_id: int, data: Dict[str, Any]) -> Optional[TaskRun]:
    """Update an existing task run in the database"""
    db = SessionLocal()
    try:
        task_run = db.query(TaskRun).filter(TaskRun.id == task_run_id).first()
        if not task_run:
            return None
        
        for key, value in data.items():
            if hasattr(task_run, key):
                setattr(task_run, key, value)
        
        db.commit()
        db.refresh(task_run)
        return task_run
    finally:
        db.close()


def create_run_step(task_run_id: int, step_number: int, data: Dict[str, Any]) -> RunStep:
    """Create a new run step in the database"""
    db = SessionLocal()
    try:
        run_step = RunStep(
            task_run_id=task_run_id,
            step_number=step_number,
            description=data.get("description"),
            screenshot=data.get("screenshot"),
        )
        db.add(run_step)
        db.commit()
        db.refresh(run_step)
        return run_step
    finally:
        db.close()


def create_run_action(task_run_id: int, step_number: int, action_number: int, data: Dict[str, Any]) -> RunAction:
    """Create a new run action in the database"""
    db = SessionLocal()
    try:
        run_action = RunAction(
            task_run_id=task_run_id,
            step_number=step_number,
            action_number=action_number,
            name=data.get("name"),
            params=data.get("params"),
            is_done=data.get("is_done", False),
            success=data.get("success"),
            extracted_content=data.get("extracted_content"),
            error=data.get("error"),
            include_in_memory=data.get("include_in_memory"),
        )
        db.add(run_action)
        db.commit()
        db.refresh(run_action)
        return run_action
    finally:
        db.close()

def update_run_step(task_run_id: int, step_number: int, data: Dict[str, Any]) -> Optional[RunStep]:
    """Update an existing run step in the database"""
    db = SessionLocal()
    try:
        run_step = db.query(RunStep).filter(
            RunStep.task_run_id == task_run_id,
            RunStep.step_number == step_number
        ).first()
        
        if not run_step:
            return None
        
        for key, value in data.items():
            if hasattr(run_step, key):
                setattr(run_step, key, value)
        
        db.commit()
        db.refresh(run_step)
        return run_step
    finally:
        db.close()

def get_task(task_id: int) -> Optional[Task]:
    """Get a task by ID"""
    db = SessionLocal()
    try:
        return db.query(Task).filter(Task.id == task_id).first()
    finally:
        db.close()


def get_all_tasks() -> List[Task]:
    """Get all tasks"""
    db = SessionLocal()
    try:
        return db.query(Task).order_by(Task.id.desc()).all()
    finally:
        db.close()


def get_task_run(task_run_id: int) -> Optional[TaskRun]:
    """Get a task run by ID"""
    db = SessionLocal()
    try:
        return db.query(TaskRun).filter(TaskRun.id == task_run_id).first()
    finally:
        db.close()


def get_task_run_with_steps(task_run_id: int) -> Optional[Dict[str, Any]]:
    """Get a task run by ID with all steps and actions eagerly loaded and converted to dict"""
    db = SessionLocal()
    try:
        task_run = db.query(TaskRun).options(
            joinedload(TaskRun.steps).joinedload(RunStep.actions)
        ).filter(TaskRun.id == task_run_id).first()

        if not task_run:
            return None

        # Convert to dict while session is still open
        return task_run.to_dict()
    finally:
        db.close()


def get_run_steps(task_run_id: int) -> List[RunStep]:
    """Get all run steps for a task run"""
    db = SessionLocal()
    try:
        return db.query(RunStep).filter(RunStep.task_run_id == task_run_id).order_by(RunStep.step_number).all()
    finally:
        db.close()


def get_run_actions(task_run_id: int, step_number: int) -> List[RunAction]:
    """Get all run actions for a specific step"""
    db = SessionLocal()
    try:
        return db.query(RunAction).filter(
            RunAction.task_run_id == task_run_id,
            RunAction.step_number == step_number
        ).order_by(RunAction.action_number).all()
    finally:
        db.close()


def get_task_runs(task_id: int) -> List[TaskRun]:
    """Get all task runs for a specific task"""
    db = SessionLocal()
    try:
        return db.query(TaskRun).filter(TaskRun.task_id == task_id).order_by(TaskRun.id.desc()).all()
    finally:
        db.close()


def create_task_and_task_run(prompt: str, model: str, provider: str, webhook_url: Optional[str] = None, response_format: Optional[str] = 'text', json_schema: Optional[str] = None, cached_workflow: Optional[Dict[str, Any]] = None, use_cached_workflow: bool = False) -> Dict[str, Any]:
    """Create a task and an associated task run by reusing existing functions"""
    task = create_task(prompt=prompt, model=model, provider=provider, webhook_url=webhook_url, response_format=response_format, json_schema=json_schema, cached_workflow=cached_workflow, use_cached_workflow=use_cached_workflow)
    task_run = create_task_run(
        task_id=task.id,
        prompt=prompt,
        model=model,
        provider=provider,
        webhook_url=webhook_url,
        response_format=response_format,
        json_schema=json_schema
    )

    return {
        "task": task,
        "task_run": task_run
    }
