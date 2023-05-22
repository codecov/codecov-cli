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
  