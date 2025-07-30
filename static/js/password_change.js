// Toggle password visibility
function togglePasswordVisibility(inputElement, iconElement) {
  const isVisible = inputElement.type === "text";
  inputElement.type = isVisible ? "password" : "text";
  iconElement.classList.replace(
    isVisible ? "bi-eye-fill" : "bi-eye-slash-fill",
    isVisible ? "bi-eye-slash-fill" : "bi-eye-fill"
  );
}

document.querySelectorAll('.view-password').forEach(button => {
  button.addEventListener('click', (e) => {
    const inputId = button.getAttribute('data-target');
    const inputElement = document.getElementById(inputId);
    const iconElement = button.querySelector('i');
    if (inputElement && iconElement){
       togglePasswordVisibility(inputElement,iconElement)
    }
  })
});

document.getElementById("cambioPassword").addEventListener("submit", function (event) {
  event.preventDefault(); // Evita el envío del formulario inicialmente

    // Obtenemos el valor de los inputs
  const password1 = document.getElementById("newPassword");
  const password2 = document.getElementById("newPasswordConf");
  const alertBox = document.getElementById("alertPassword");

  if (password1.value !== password2.value) {
    alertBox.classList.remove("d-none"); // Muestra la alerta
    //password1.classList.add("is-invalid");
    password2.classList.add("is-invalid");
  } else {
    alertBox.classList.add("d-none"); // Oculta la alerta si todo está bien
    //password1.classList.remove("is-invalid");
    password2.classList.remove("is-invalid");

    this.submit(); // Envía el formulario si todo está correcto
  }
});