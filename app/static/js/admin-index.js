const copyEvent = (id) => {
  let str = document.getElementById(id);
  window.getSelection().selectAllChildren(str);
  document.execCommand('Copy');
}

// For copying and pasting names just on one click
// Help, nothing renders anymore