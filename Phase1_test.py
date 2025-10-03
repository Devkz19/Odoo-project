# # 1. Create a dictionary of employees with (name, role, salary). Print only salaries > 30k.
employees = {
    "Dev": {"role": "developer","salary": 20000},
    "Ajay": {"role": "Tester","salary": 40000},
    "komal": {"role": "Team Lead","salary": 60000}
}
for emp in employees:
    if employees[emp]["salary"]>30000:
        print(f"employee name: {emp} salary: {employees[emp]['salary']}")

# Output:employee name: Ajay salary: 40000
#        employee name: komal salary: 60000
     
        
# # 2. Create a tuple of 5 elements, try modifying it, and note the error.
tuple = (1,2,3,4,5)
print(tuple)
tuple[0] = 5
print(tuple)

# # Error : TypeError: 'tuple' object does not support item assignment


# # 3. Write a program to swap two numbers without a third variable.
a = 5
b = 10
a,b = b,a

print(a,b)
# # Output: 10, 5


# # 4 Reverse a string without using slicing.
string = "Dev"
rev_string = ""
for i in range(len(string)-1,-1,-1):
    rev_string += string[i]
    print(rev_string)
    
# # output : v
# #          ve
# #          veD


# # 5. Print current date in format YYYY-MM-DD.
from datetime import date
today = date.today()
print("Current date:",today)

# # output : Current date: 2025-10-01


# # 6. Function with **kwargs to print employee details.
def employee_details(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")
        
employee_details(name='Dev', age=22, role='Developer')

# output :name: Dev
#         age: 22
#         role: Developer
        
      
# # 7. Write a lambda function to filter even numbers from a list.
numbers = [1,2,3,4,5,6,7,8,9,10]
even_number = list(filter(lambda x:x%2==0,numbers))
print(even_number)

# # output: [2, 4, 6, 8, 10]


# # 8. Create a class Product with fields: name, price. Add method to apply discount.Inherit Electronics from Product, add warranty period.Create 3 different product objects and print final price after discount.
class Product:
    def __init__(self,name,price):
        self.name = name
        self.price = price
        
    def apply_discount(self,discount):
        self.price -= discount
        return self.price
class Electronics (Product):
    def __init__(self,name,price,warranty):
        super().__init__(name,price)
        self.warranty = warranty
        
product1 = Electronics("Laptop",30000,2)
product2 = Electronics("Smartphone",18000,1)

print(f"Final Price of {product1.name} after discount: ${product1.apply_discount(100)}")
print(f"Final Price of {product2.name} after discount: ${product2.apply_discount(100)}")

# output : Final Price of Laptop after discount: $29900
#          Final Price of Smartphone after discount: $17900

        
# # 9. Create Shape base class with method area(). Inherit Circle and Rectangle with their own area() implementation.
class Shape:
    def area(self):
        pass
    
class Circle(Shape):
    def __init__(self,radius):
        self.radius = radius
        
    def area(self):
        return 3.14 * self.radius * self.radius
    
class Rectangle(Shape):
    def __init__(self,length,width):
        self.length = length
        self.width = width
        
    def area(self):
        return (self.length * self.width)   
circle = Circle(5)
rectangle = Rectangle(4,6)

print(f"Area of Circle : {circle.area()}")
print(f"Area of Rectangle : {rectangle.area()}")  

# output : Area of Circle : 78.5
#          Area of Rectangle : 24

               
# 10. Create a class method (@classmethod) to count number of objects created
class Counter:
    count = 0
    
    def __init__(self):
        Counter.count += 1
        
    @classmethod
    def get_count(cls):
        return cls.count
obj1 = Counter()
obj2 = Counter()
obj3 = Counter()
print(Counter.get_count())

# Output : 3

 
# # 11. Store student data in JSON
import json

student = {
    "name": "Dev",
    "age": 22,
    "city": "Surat"
}
student_json = json.dumps(student, indent=5)
print(student_json)

# output : {
#      "name": "Dev",
#      "age": 22,
#      "city": "Surat"
# }


# # 12. Export student data to CSV.
import csv 

student_data = [
    {"name": "Dev","age":22,"city":"Surat"},
    {"name": "Kamesh","age":25,"city":"Ahemdabad"},
]

student_data_csv = "student_data.csv"

with open(student_data_csv, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['name','age','city'])
    writer.writeheader()
    writer.writerows(student_data)

with open(student_data_csv, mode='r') as file:
    print(file.read())

# #output - file created : student_data.csv
   

# # 13. Build Student CRUD app in Python
import sqlite3

# Connect to SQLite database (creates file if not exists)
conn = sqlite3.connect("students.db")
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    roll TEXT PRIMARY KEY,
    name TEXT,
    age INTEGER,
    course TEXT
)
''')
conn.commit()

def create_student():
    roll = input("Enter Roll Number: ")
    name = input("Enter Name: ")
    age = input("Enter Age: ")
    course = input("Enter Course: ")
    try:
        cursor.execute("INSERT INTO students VALUES (?, ?, ?, ?)", (roll, name, age, course))
        conn.commit()
        print("Student added successfully!")
    except sqlite3.IntegrityError:
        print("Student with this roll number already exists!")

def read_students():
    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    if not rows:
        print("No students found.")
        return
    print("\n Student Records ")
    for row in rows:
        print(f"Roll: {row[0]}, Name: {row[1]}, Age: {row[2]}, Course: {row[3]}")

def update_student():
    roll = input("Enter Roll Number to update: ")
    name = input("Enter New Name: ")
    age = input("Enter New Age: ")
    course = input("Enter New Course: ")
    cursor.execute("UPDATE students SET name=?, age=?, course=? WHERE roll=?", (name, age, course, roll))
    if cursor.rowcount == 0:
        print("Student not found!")
    else:
        conn.commit()
        print("Student updated successfully!")

def delete_student():
    roll = input("Enter Roll Number to delete: ")
    cursor.execute("DELETE FROM students WHERE roll=?", (roll,))
    if cursor.rowcount == 0:
        print("Student not found!")
    else:
        conn.commit()
        print("Student deleted successfully!")

def menu():
    while True:
        print("\nStudent CRUD App")
        print("1. Create Student")
        print("2. Read Students")
        print("3. Update Student")
        print("4. Delete Student")
        print("5. Exit")

        choice = input("Enter choice: ")
        if choice == "1":
            create_student()
        elif choice == "2":
            read_students()
        elif choice == "3":
            update_student()
        elif choice == "4":
            delete_student()
        elif choice == "5":
            print(" Exiting...")
            break
        else:
            print(" Invalid choice!")

# Run the app
menu()


# # 14. Write a generator that yields even numbers up to 100.
def even_number():
    for i in range(1,101):
        if i%2==0:
            yield i
    
for num in even_number():
                print(num)

# output :    2
#             4
#             6
#             8
#             10
#             12
#             14
#             16
#             18
#             20
#             22
#             24
#             26
#             28
#             30
#             32
#             34
#             36
#             38
#             40
#             42
#             44
#             46
#             48
#             50
#             52
#             54
#             56
#             58
#             60
#             62
#             64
#             66
#             68
#             70
#             72
#             74
#             76
#             78
#             80
#             82
#             84
#             86
#             88
#             90
#             92
#             94
#             96
#             98
#             100              
                
# # 15. Create a decorator to log function execution time.
import time
def log_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time of {func.__name__}: {execution_time} seconds")
        return result
    return wrapper

@log_execution_time
def sample_function(n):
    time.sleep(n)
    return f"Slept for {n} seconds"

result = sample_function(5)
print(result)

# output : Execution time of sample_function: 5.0001137256622314 seconds
# Slept for 5 seconds

            
# # 16. Create a custom iterator that returns numbers 1–5.
class CustomIterator:
    def __init__(self):
        self.num = 1
        
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.num < 6:
            current_num = self.num
            self.num += 1
            return current_num
        else:
            raise StopIteration
custom_iterator = CustomIterator()
for number in custom_iterator:
    print(number)
    
# # output :1
# #         2
# #         3
# #         4
# #         5    


# # 17 Write a dictionary comprehension to map numbers 1–5 to their squares.
squares = {x: x**2 for x in range(1,6)}
print(squares)

# # output : {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

# # 18. Use regex to extract all email addresses from a string.
import re

email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

def validate_email(email_address):
    if re.fullmatch(email_pattern, email_address):
        return True
    else:
        return False

print(validate_email("dev@gmail.com"))  
print(validate_email("devgmail.com"))

# output: True
#         False  


# # 19. Convert Python dict into JSON and save to file.
import json

student = {
    "name": "Dev",
    "age": 22,
    "city": "Surat"
}
student_json = json.dumps(student, indent=5)
print(student_json)
with open('student.json', 'w') as json_file:
    json_file.write(student_json)

# output : {} student.json file created     

# # 20 Read a CSV of employees (id, name, salary) and print those with salary > 50k.
import csv

with open("employee.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if int(row["salary"]) > 50000:
            print(row["name"], row["salary"])