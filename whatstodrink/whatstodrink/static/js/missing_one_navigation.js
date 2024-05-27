function MissingOneNavigation() {

    const selectElement = document.getElementById("jump_to");

    if (selectElement) {
        selectElement.addEventListener("change", function(event) {

            const selectedOption = event.target.options[event.target.selectedIndex];
            const targetId = selectedOption.getAttribute("data-target");

            if (targetId) {
                const targetElement = document.getElementById(targetId);

                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    }
}

document.addEventListener("htmx:afterSettle", MissingOneNavigation);