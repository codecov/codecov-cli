function outerFunction() {
  
    function innerFunction() {
      console.log("Inner function called");
    }
    innerFunction();
  }
  
outerFunction();

async function foo() {}

class Foo {
  async bar() {}
}

// arrow function 
async (a) => { return foo; };

// 
async function* foo() { yield 1; }

function a () { function b () {} function *c () {} class D {} return }

[
    function *() {},
    function *generateStuff(arg1, arg2) {
      yield;
      yield arg2;
      yield * foo();
    }
]

var b = function() {};
  
var fruit = "apple";

switch (fruit) {
  case "apple":
    console.log("It's an apple.");
    break;
  case "banana":
    console.log("It's a banana.");
    console.log("It's a banana.");
    break;
  case "orange":
    console.log("It's an orange.");
    break;
  default:
    console.log("It's an unknown fruit.");
}

var i = 0;
do {
  console.log("The value of i is: " + i);
  i++;
} while (i < 5);

do
  console.log("The value of i is: " + i);
while (i < 5);

do 
  for (j = 0; j < i; j++) console.log('X');
while (i < 5);