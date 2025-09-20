import { useState } from 'react';
import './Navbar.css';
import {Link} from 'react-router-dom';

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);


  return (
    <nav className="navbar">
      <div className="hamburger" onClick={() => setIsOpen(!isOpen)}>
        <div className="bar" />
        <div className="bar" />
        <div className="bar" />
      </div>

      {/* Dropdown menu */}
      {isOpen && (
        <div className="menu">
          <Link onClick={() => setIsOpen(false)} to="/">Home</Link>
          <Link onClick={() => setIsOpen(false)} smooth to="/#about">About</Link>
          <Link onClick={() => setIsOpen(false)} to="http://127.0.0.1:5001">Control</Link>
        </div>
      )}
    </nav>
  );
}

export default Navbar;
