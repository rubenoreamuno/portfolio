"""
ETL Pipeline Framework
Abstract pipeline definition with dependency management
"""

from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Task:
    """Pipeline task definition"""
    name: str
    function: Callable
    depends_on: List[str] = None
    retries: int = 3
    retry_delay: int = 60
    timeout: Optional[int] = None
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []

class ETLPipeline:
    """ETL Pipeline orchestrator"""
    
    def __init__(self, name: str, schedule: str = None, 
                 max_retries: int = 3, timeout: int = 3600):
        self.name = name
        self.schedule = schedule
        self.max_retries = max_retries
        self.timeout = timeout
        self.tasks: Dict[str, Task] = {}
        self.execution_history: List[Dict] = []
    
    def add_task(self, name: str, function: Callable, 
                depends_on: List[str] = None, retries: int = 3,
                timeout: Optional[int] = None) -> 'ETLPipeline':
        """Add a task to the pipeline"""
        task = Task(
            name=name,
            function=function,
            depends_on=depends_on or [],
            retries=retries,
            timeout=timeout or self.timeout
        )
        self.tasks[name] = task
        return self
    
    def get_task_dependencies(self, task_name: str) -> List[str]:
        """Get all dependencies for a task (recursive)"""
        task = self.tasks.get(task_name)
        if not task:
            return []
        
        dependencies = set(task.depends_on)
        for dep in task.depends_on:
            dependencies.update(self.get_task_dependencies(dep))
        
        return list(dependencies)
    
    def get_execution_order(self) -> List[str]:
        """Get tasks in execution order (topological sort)"""
        # Simple topological sort
        in_degree = {name: len(task.depends_on) for name, task in self.tasks.items()}
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            task_name = queue.pop(0)
            result.append(task_name)
            
            # Update in-degrees
            for name, task in self.tasks.items():
                if task_name in task.depends_on:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)
        
        if len(result) != len(self.tasks):
            raise ValueError("Circular dependency detected in pipeline")
        
        return result
    
    def execute_task(self, task: Task, context: Dict = None) -> bool:
        """Execute a single task"""
        context = context or {}
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        try:
            # Execute task function
            result = task.function(**context)
            
            task.status = TaskStatus.SUCCESS
            task.end_time = datetime.now()
            return True
        
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()
            return False
    
    def execute(self, context: Dict = None) -> Dict:
        """Execute the entire pipeline"""
        context = context or {}
        execution_id = datetime.now().isoformat()
        
        execution_log = {
            'execution_id': execution_id,
            'pipeline_name': self.name,
            'start_time': datetime.now().isoformat(),
            'tasks': {}
        }
        
        execution_order = self.get_execution_order()
        
        for task_name in execution_order:
            task = self.tasks[task_name]
            
            # Check dependencies
            all_deps_success = all(
                self.tasks[dep].status == TaskStatus.SUCCESS
                for dep in task.depends_on
            )
            
            if not all_deps_success and task.depends_on:
                task.status = TaskStatus.SKIPPED
                execution_log['tasks'][task_name] = {
                    'status': 'skipped',
                    'reason': 'Dependency failed'
                }
                continue
            
            # Execute task with retries
            success = False
            for attempt in range(task.retries + 1):
                if attempt > 0:
                    print(f"Retrying task {task_name} (attempt {attempt + 1})")
                
                success = self.execute_task(task, context)
                
                if success:
                    break
                
                if attempt < task.retries:
                    import time
                    time.sleep(task.retry_delay)
            
            execution_log['tasks'][task_name] = {
                'status': task.status.value,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'duration_seconds': (task.end_time - task.start_time).total_seconds() if task.end_time and task.start_time else None,
                'error': task.error
            }
            
            if not success:
                execution_log['status'] = 'failed'
                execution_log['failed_task'] = task_name
                break
        
        if execution_log.get('status') != 'failed':
            execution_log['status'] = 'success'
        
        execution_log['end_time'] = datetime.now().isoformat()
        self.execution_history.append(execution_log)
        
        return execution_log
    
    def get_status(self) -> Dict:
        """Get current pipeline status"""
        return {
            'name': self.name,
            'total_tasks': len(self.tasks),
            'task_statuses': {name: task.status.value for name, task in self.tasks.items()},
            'last_execution': self.execution_history[-1] if self.execution_history else None
        }

# Example usage
def extract_data():
    print("Extracting data...")
    return {"data": "extracted"}

def transform_data(data):
    print(f"Transforming data: {data}")
    return {"data": "transformed"}

def load_data(data):
    print(f"Loading data: {data}")
    return {"status": "loaded"}

if __name__ == "__main__":
    # Create pipeline
    pipeline = ETLPipeline(name="example_etl", schedule="0 2 * * *")
    
    # Add tasks
    pipeline.add_task("extract", extract_data)
    pipeline.add_task("transform", lambda: transform_data({"data": "extracted"}), 
                     depends_on=["extract"])
    pipeline.add_task("load", lambda: load_data({"data": "transformed"}), 
                     depends_on=["transform"])
    
    # Execute
    result = pipeline.execute()
    print(f"\nExecution result: {result['status']}")

