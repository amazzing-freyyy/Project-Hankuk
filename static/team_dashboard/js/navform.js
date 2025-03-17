const parents = document.querySelectorAll(".form-group");
let currentIndex = 0;

const backbtn = document.getElementById('back');
const nextbtn = document.getElementById('next');
const submitbtn = document.getElementById('submit');
backbtn.disabled = false;
nextbtn.disabled = false;
submitbtn.disabled = true;

function showParent(index) {
    parents.forEach(parent => parent.classList.add("d-none"));
    parents[index].classList.remove("d-none");

    if (currentIndex == 0){
        backbtn.disabled = true;
        nextbtn.disabled = false;
        submitbtn.disabled = true;
    }else if(currentIndex == (parents.length-1)){
        backbtn.disabled = false;
        nextbtn.disabled = true;
        submitbtn.disabled = false;
    }else{
        backbtn.disabled = false;
        nextbtn.disabled = false;
        submitbtn.disabled = true;
    }
}

function nextParent() {
    currentIndex = (currentIndex + 1) % parents.length;
    showParent(currentIndex);
}

function prevParent() {
    currentIndex = (currentIndex - 1 + parents.length) % parents.length;
    showParent(currentIndex);
}

showParent(currentIndex);
