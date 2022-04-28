const cursorInFocus = (input) =>{
  setTimeout(function(){input.focus()}, 500);
}

const cursorInFocusFromLabel = (input) =>{
  let val = input.getAttribute("for");
  setTimeout(function(){document.getElementById(val).focus()}, 500);
}