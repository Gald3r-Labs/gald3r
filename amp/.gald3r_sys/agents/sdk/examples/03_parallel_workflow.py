"""
Example 3: Parallel Multi-Agent Workflow

Demonstrates:
- Running multiple agents in parallel
- Handling independent tasks concurrently
- Aggregating parallel results
- Error handling in parallel execution
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from context import AgentContext
from workflow import AgentWorkflow


class MicroserviceAgent(BaseAgent):
    """Generic microservice implementation agent"""

    def __init__(self, service_name: str):
        super().__init__(
            name=f"microservice-{service_name}",
            description=f"Implement {service_name} microservice",
            tools=["Read", "Write", "Edit", "Bash"]
        )
        self.service_name = service_name

    def process(self, context: AgentContext):
        task = context.get("task")
        self.logger.info(f"Implementing {self.service_name} microservice")

        # Simulate microservice implementation
        import time
        time.sleep(1)  # Simulate work

        service_info = {
            "name": self.service_name,
            "endpoints": [
                f"/api/{self.service_name}/create",
                f"/api/{self.service_name}/read",
                f"/api/{self.service_name}/update",
                f"/api/{self.service_name}/delete"
            ],
            "database": f"{self.service_name}_db",
            "tests_passing": True
        }

        # Update context with service info
        context.set(f"{self.service_name}_service", service_info)

        return {
            "status": "completed",
            "service": self.service_name,
            "endpoints": len(service_info["endpoints"]),
            "tests_passing": True
        }


def main():
    print("=" * 60)
    print("Example 3: Parallel Multi-Agent Workflow")
    print("=" * 60)

    # Create workflow
    workflow = AgentWorkflow(
        max_parallel_agents=5,
        enable_progress_tracking=True
    )

    # Create context
    context = workflow.create_context(
        task="Build microservices architecture with 5 services",
        priority="high"
    )

    print(f"\nWorkflow ID: {context.workflow_id}")
    print(f"Task: {context.task}")

    # Define services to build in parallel
    services = ["auth", "users", "products", "orders", "payments"]

    agents = [
        (f"microservice-{service}", MicroserviceAgent(service))
        for service in services
    ]

    print(f"\nBuilding {len(agents)} microservices in parallel...")
    print("-" * 60)

    # Run workflow
    import time
    start_time = time.time()

    result = workflow.run_parallel(agents, context)

    end_time = time.time()
    duration = end_time - start_time

    # Display results
    print("\n" + "=" * 60)
    print("Workflow Result:")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Agents Completed: {len(result['agents_completed'])}")
    print(f"Agents Failed: {len(result['agents_failed'])}")

    if result['agents_completed']:
        print(f"\nCompleted Services:")
        for agent in result['agents_completed']:
            print(f"  ✓ {agent}")

    if result['agents_failed']:
        print(f"\nFailed Services:")
        for agent in result['agents_failed']:
            print(f"  ✗ {agent}")

    print("\n" + "-" * 60)
    print("Service Details:")
    print("-" * 60)

    for service in services:
        service_info = context.get(f"{service}_service")
        if service_info:
            print(f"\n{service.upper()} Service:")
            print(f"  Endpoints: {len(service_info['endpoints'])}")
            print(f"  Database: {service_info['database']}")
            print(f"  Tests: {'✓ Passing' if service_info['tests_passing'] else '✗ Failing'}")

    # Calculate total endpoints
    total_endpoints = sum(
        len(context.get(f"{service}_service", {}).get("endpoints", []))
        for service in services
    )

    print("\n" + "-" * 60)
    print("Summary:")
    print("-" * 60)
    print(f"Services Built: {len(result['agents_completed'])}")
    print(f"Total Endpoints: {total_endpoints}")
    print(f"Total Duration: {duration:.2f} seconds")
    print(f"Avg Time/Service: {duration / len(services):.2f} seconds")

    # Archive workflow
    print(f"\nArchiving workflow...")
    workflow.archive_workflow(context.workflow_id)

    print("\n✓ Example completed successfully!")
    print(f"\nNote: Running {len(services)} agents in parallel completed in {duration:.2f}s")
    print(f"Sequential execution would take ~{len(services):.0f}s (1s per service)")


if __name__ == "__main__":
    main()
