// comment for trial
import React from 'react';
import Navbar from '../components/Navbar';
import Starfield from '../components/Starfield';

function Team() {
  return (
    <div style={{ 
      position: 'relative',
      backgroundColor: '000', 
      minHeight: "100vh", 
      color: "#fff", 
      textAlign: "center",
      overflow: "hidden"
    }}>
      <Starfield />

      <div style={{
        position: 'relative',
        zIndex: -0.5
      }}>
        <Navbar />

        {/* Styled header box around the heading */}
        <div style={{
          backgroundColor: "#1118278a",
          color: "white",
          padding: "20px",
          borderRadius: "12px",
          boxShadow: "0 0 10px #3f6293",
          margin: "60px auto 0",
          width: "fit-content",
          maxWidth: "90%",
        }}>
          <h1 style={{ fontSize: "3rem", margin: 0 }}>
            Meet the Team
          </h1>
        </div>

        {/* Team member container */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          flexWrap: 'wrap',
          columnGap: '100px',
          rowGap: '90px',
          padding: '0 20px',
          marginTop: '100px'
        }}>
          {[
            {
              name: "Vidit Naik",
              role: "Project Manager",
              image: "vidit.png"
            },
            {
              name: "Khushi Kaushik",
              role: "Backend Developer",
              image: "/khushiheadshot.jpeg"
            },
            {
              name: "Evan Miller",
              role: "UI/UX Designer",
              image: "evan.jpg"
            },
            {
              name: "Riya Jain",
              role: "Software Engineer",
              image: "Headshot.JPG"
            }
          ].map((member, index) => (
            <div key={index} style={{ 
              width: "250px", 
              textAlign: "center"
            }}>
              <img 
                src={member.image} 
                alt={member.name} 
                style={{
                  width: "250px",
                  height: "250px",
                  objectFit: "cover",
                  borderRadius: "50%",
                  border: "2px solid #fff",
                  marginBottom: "10px"
                }} 
              />
              <h3 style={{ marginBottom: "5px" }}>{member.name}</h3>
              <p style={{ fontSize: "0.95rem", color: "#ccc" }}>{member.role}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Team;
