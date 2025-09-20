import Navbar from '../components/Navbar';
import Starfield from '../components/Starfield';
import DroneControl from '../components/DroneControl';

function Control(){
    return (
        <>
            <div style={{display: "block", width: "100%"}}>
                <Navbar />
            </div>
            <Starfield />
            <DroneControl />
        </>
    );
}

export default Control;