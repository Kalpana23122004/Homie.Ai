const sections = document.querySelectorAll("section");

window.addEventListener("scroll", () => {

sections.forEach(section => {

const top = window.scrollY;
const offset = section.offsetTop - 300;
const height = section.offsetHeight;

if(top >= offset && top < offset + height){
section.classList.add("show");
}

});

});
