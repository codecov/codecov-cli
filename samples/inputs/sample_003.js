function myFunction(p1, p2) {
  return p1 * p2;   // The function returns the product of p1 and p2
}

// Variable declaration and assignment
let x = 10;
const PI = 3.14159;
var y = "Hello";

// Function declaration and invocation
function add(a, b) {
  return a + b;
}

let result = add(x, 5);

// Conditional statements
if (x > 0) {
  console.log("x is positive");
} else if (x < 0) {
  console.log("x is negative");
} else {
  console.log("x is zero");
}

// Looping constructs
for (let i = 0; i < 5; i++) {
  console.log(i);
}

let numbers = [1, 2, 3, 4, 5];
for (let number of numbers) {
  console.log(number);
}

// Objects and properties
let person = {
  name: "John",
  age: 30,
  address: {
    street: "123 Main St",
    city: "New York",
  },
};

console.log(person.name);
console.log(person.address.city);

// Arrays and array methods
let fruits = ["apple", "banana", "orange"];
fruits.push("grape");
console.log(fruits.length);

// Classes and inheritance
class Shape {
  constructor(color) {
    this.color = color;
  }

  getColor() {
    return this.color;
  }
}

class Circle extends Shape {
  constructor(color, radius) {
    super(color);
    this.radius = radius;
  }

  getArea() {
    return Math.PI * this.radius * this.radius;
  }
}

let myCircle = new Circle("red", 5);
console.log(myCircle.getColor());
console.log(myCircle.getArea());

// Promises and async/await
function fetchData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve("Data received");
    }, 2000);
  });
}

async function getData() {
  try {
    let data = await fetchData();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

getData();