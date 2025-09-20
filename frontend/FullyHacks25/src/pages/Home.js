import Header from "../components/Header";
import About from "../components/About";
import Team from "../components/Team";
import { useLocation } from 'react-router-dom';
import {useEffect } from 'react';

function Home() {
    const location = useLocation();
    useEffect(() => {
        if (location.hash === "#about") {
          const aboutElem = document.getElementById('about');
          if (aboutElem) {
            // Scroll smoothly into view
            aboutElem.scrollIntoView({ behavior: "smooth" });
          }
        }
    }, [location]);
    return (
    <>
        <Header/>
        <About />
        <Team />
    </>
  );
}

export default Home;
