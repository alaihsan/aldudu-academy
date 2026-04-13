// Dynamic Educational Quotes with Typing Effect
const educationalQuotes = [
    "Lanjutkan perjalanan belajarmu hari ini. Kamu memiliki beberapa aktivitas yang menunggu.",
    "Pendidikan adalah senjata paling mematikan di dunia, karena dengan pendidikan Anda dapat mengubah dunia.",
    "Perjalanan ribuan mil dimulai dengan satu langkah. Mulailah belajar hari ini!",
    "Investasi terbaik adalah investasi dalam pengetahuan dirimu sendiri.",
    "Pendidikan bukan persiapan untuk hidup; pendidikan adalah kehidupan itu sendiri.",
    "Akar pendidikan memang pahit, tapi buahnya manis.",
    "Belajar tanpa berpikir itu sia-sia. Berpikir tanpa belajar itu berbahaya.",
    "Pendidikan adalah tiket ke masa depan. Hari esok milik orang yang mempersiapkannya hari ini.",
    "Jangan berhenti belajar, karena hidup tidak pernah berhenti mengajarkan.",
    "Pendidikan adalah cahaya yang menerangi dunia.",
    "Orang yang berhenti belajar adalah orang yang sudah tua, meskipun usianya masih muda.",
    "Belajar adalah harta karun yang akan mengikuti pemiliknya ke mana saja.",
    "Pendidikan membantu kita menjadi siapa kita sebenarnya.",
    "Kegagalan adalah bumbu yang memberi rasa pada pendidikan.",
    "Pendidikan adalah proses seumur hidup dari kelahiran hingga kematian.",
    "Belajar tanpa batas adalah kunci untuk meraih impianmu.",
    "Pendidikan bukan hanya mengisi ember, tapi menyalakan api.",
    "Setiap buku adalah pintu ke dunia baru. Membacalah, belajarlah, tumbuhlah.",
    "Pendidikan adalah kekuatan untuk mengubah dunia menjadi lebih baik.",
    "Belajar hari ini, memimpin besok. Masa depanmu dimulai sekarang."
];

// localStorage keys
const QUOTE_INDEX_KEY = 'aldudu_quote_index';
const QUOTE_TIMESTAMP_KEY = 'aldudu_quote_timestamp';
const QUOTE_INTERVAL = 10000; // 10 seconds

// Get current quote index from localStorage or start fresh
function getCurrentQuoteIndex() {
    const storedIndex = localStorage.getItem(QUOTE_INDEX_KEY);
    const storedTime = localStorage.getItem(QUOTE_TIMESTAMP_KEY);
    const now = Date.now();

    // If no stored data or it's been more than 10 seconds since last change
    if (!storedIndex || !storedTime || (now - parseInt(storedTime)) >= QUOTE_INTERVAL) {
        let newIndex;
        if (storedIndex !== null) {
            // Get next quote, loop back to 0 if at end
            newIndex = (parseInt(storedIndex) + 1) % educationalQuotes.length;
        } else {
            // First time - random start
            newIndex = Math.floor(Math.random() * educationalQuotes.length);
        }

        // Save new index and timestamp
        localStorage.setItem(QUOTE_INDEX_KEY, newIndex.toString());
        localStorage.setItem(QUOTE_TIMESTAMP_KEY, now.toString());

        return newIndex;
    }

    // Still within 10 seconds, keep current quote
    return parseInt(storedIndex);
}

// Typewriter effect for multi-line text
function typeWriter(text, element, speed = 50) {
    let i = 0;
    element.textContent = '';
    element.classList.remove('typing-complete');
    element.classList.add('typing-active');

    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(() => type(), speed);
        } else {
            element.classList.remove('typing-active');
            element.classList.add('typing-complete');
        }
    }

    type();
}

// Update quote with typing effect
function updateQuote() {
    const quoteElement = document.getElementById('dynamic-quote');
    if (!quoteElement) return;

    const index = getCurrentQuoteIndex();
    const quote = educationalQuotes[index];

    // Calculate typing speed based on quote length (faster for longer quotes)
    const typingSpeed = Math.max(30, Math.min(80, 4000 / quote.length));

    // Fade out
    quoteElement.classList.add('quote-fade');

    // After fade out, change text and fade in
    setTimeout(() => {
        quoteElement.innerHTML = '<span class="typing-text"></span>';

        const textSpan = quoteElement.querySelector('.typing-text');
        quoteElement.classList.remove('quote-fade');
        quoteElement.style.animation = 'fadeIn 0.5s ease-out forwards';

        // Start typing effect
        typeWriter(quote, textSpan, typingSpeed);

        // Remove animation class after completion
        setTimeout(() => {
            quoteElement.style.animation = '';
        }, 500);

        // Update timestamp
        localStorage.setItem(QUOTE_TIMESTAMP_KEY, Date.now().toString());
    }, 500);
}

// Check for quote update - handles background tab scenario
function checkQuoteUpdate() {
    const storedTime = localStorage.getItem(QUOTE_TIMESTAMP_KEY);
    const now = Date.now();

    // If more than 10 seconds since last update, refresh quote
    if (!storedTime || (now - parseInt(storedTime)) >= QUOTE_INTERVAL) {
        updateQuote();
    }
}

// Initialize dynamic quotes
let quoteCheckInterval;

document.addEventListener('DOMContentLoaded', function() {
    // Initial quote
    setTimeout(updateQuote, 100);

    // Check every 2 seconds if quote needs updating (handles background tabs)
    quoteCheckInterval = setInterval(checkQuoteUpdate, 2000);

    // Also update when page becomes visible again
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            checkQuoteUpdate();
        }
    });

    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        clearInterval(quoteCheckInterval);
    });
});
