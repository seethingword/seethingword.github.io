/**
 * Background Slideshow Script
 * Creates smooth transitions between background images
 * Eliminates flashing by preloading images and using opacity transitions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Array of background images
    const backgroundImages = [
        'images/background.jpeg',
        'images/background2.jpg',
        'images/background3.jpg',
        'images/background4.jpg',
        'images/background5.jpg',
        'images/background6.jpg'
    ];

    let currentImageIndex = 0;
    const transitionDuration = 10000; // 10 seconds per image
    const fadeTime = 2000; // 2 seconds fade transition

    // Create slideshow container
    const slideshowContainer = document.createElement('div');
    slideshowContainer.className = 'background-slideshow';
    document.body.insertBefore(slideshowContainer, document.body.firstChild);

    // Preload all images and create slide elements
    const slides = [];
    let imagesLoaded = 0;

    backgroundImages.forEach((imagePath, index) => {
        // Create slide element
        const slide = document.createElement('div');
        slide.className = 'background-slide';
        slide.style.backgroundImage = `url('${imagePath}')`;
        
        // Set first image as active
        if (index === 0) {
            slide.classList.add('active');
        }
        
        slideshowContainer.appendChild(slide);
        slides.push(slide);

        // Preload image to prevent flashing
        const img = new Image();
        img.onload = function() {
            imagesLoaded++;
            // Start slideshow once all images are loaded
            if (imagesLoaded === backgroundImages.length) {
                startSlideshow();
            }
        };
        img.onerror = function() {
            console.warn(`Failed to load background image: ${imagePath}`);
            imagesLoaded++;
            if (imagesLoaded === backgroundImages.length) {
                startSlideshow();
            }
        };
        img.src = imagePath;
    });

    function startSlideshow() {
        // Only start if we have more than one image
        if (backgroundImages.length <= 1) return;

        setInterval(() => {
            // Remove active class from current slide
            slides[currentImageIndex].classList.remove('active');
            
            // Move to next image
            currentImageIndex = (currentImageIndex + 1) % backgroundImages.length;
            
            // Add active class to new slide
            slides[currentImageIndex].classList.add('active');
        }, transitionDuration);
    }

    // Fallback: start slideshow after 5 seconds even if some images fail to load
    setTimeout(() => {
        if (imagesLoaded < backgroundImages.length) {
            console.warn('Some background images failed to load, starting slideshow anyway');
            startSlideshow();
        }
    }, 5000);
});
