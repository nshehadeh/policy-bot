from langchain_core.runnables.history import RunnableWithMessageHistory

# List all attributes and methods
methods = dir(RunnableWithMessageHistory)

# Filter out private and special methods if needed
public_methods = [method for method in methods if not method.startswith('__')]

print(public_methods)