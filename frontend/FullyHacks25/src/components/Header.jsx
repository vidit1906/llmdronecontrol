import earthVideo from '../assets/earth.mp4';
import { FaChevronDown } from 'react-icons/fa';
import Navbar from './Navbar';

function Header(){

    const scrollToAbout = () => {
        const aboutElem = document.getElementById('about');
        if (aboutElem) {
          aboutElem.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <header>
            <div style={{width: "100%", height: "100vh", position: "relative"}}>
                <video style={{width: "100%", height: "100%"}} autoPlay muted loop>
                    <source src={earthVideo} type="video/mp4"/>
                </video>
                <div style={{display: 'flex', width: '100%'}}>
                    <Navbar />
                </div>
                <div style={{
                    position: 'absolute',
                    bottom: '30px',
                    width: '100%',
                    color: 'white',
                    textAlign: 'center',
                    fontSize: '3rem'
                }}>
                    <div style={{fontSize: '100px'}}>
                        Altivue
                    </div>
                    <br/>
                    <br/>
                    <div onClick={scrollToAbout}>
                        <FaChevronDown style={{fontSize: '3rem', cursor: 'pointer'}}/>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;