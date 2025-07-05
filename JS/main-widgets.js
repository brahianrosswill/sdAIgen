function toggleContainer() {
    const SHOW_CLASS = 'showed';
    const elements = {
        downloadContainer: document.querySelector('.container_cdl'),
        info: document.querySelector('.info'),
        empowerment: document.querySelector('.empowerment')
    };

    elements.downloadContainer.classList.toggle('expanded');
    elements.info.classList.toggle(SHOW_CLASS);
    elements.empowerment.classList.toggle(SHOW_CLASS);
}