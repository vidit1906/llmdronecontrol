import Navbar from '../components/Navbar';
import Starfield from '../components/Starfield';

function About(){
    return (
        <div style={{display: "block", width: "100%"}}>
            <Navbar />
            <div style={{
                maxWidth: '800px',
                margin: '80px auto',
                padding: '0 20px',
                color: '#fff',
                textAlign: 'center'
            }}>
                <h1 style={{
                    fontSize: '3rem',
                    marginBottom: '20px',
                    color: '#fff'
                }}>
                    About Us
                </h1>
                <p style={{
                    fontSize: '1.2rem',
                    lineHeight: '1.8'
                }}>
                    Welcome to <strong>Altivue</strong> — where innovation meets insight. Our mission is to provide 
                    forward-thinking solutions powered by technology that empower individuals and organizations to see 
                    the world more clearly, make smarter decisions, and connect more deeply with the things that matter. 
                    At Altivue, we believe in turning complex data into intuitive, visual experiences that spark action and inspire change.
                </p>
            </div>
        </div>
    );
}

export default About;
