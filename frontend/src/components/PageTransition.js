import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

const PageTransition = ({ children }) => {
  const location = useLocation();
  const [displayChildren, setDisplayChildren] = useState(children);
  const [transitionStage, setTransitionStage] = useState('fadeIn');

  useEffect(() => {
    if (children !== displayChildren) {
      setTransitionStage('fadeOut');
    }
  }, [children, displayChildren]);

  const handleAnimationEnd = () => {
    if (transitionStage === 'fadeOut') {
      setDisplayChildren(children);
      setTransitionStage('fadeIn');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div
      className={`transition-all duration-300 ease-out ${
        transitionStage === 'fadeIn' 
          ? 'opacity-100 translate-y-0' 
          : 'opacity-0 translate-y-2'
      }`}
      onTransitionEnd={handleAnimationEnd}
    >
      {displayChildren}
    </div>
  );
};

export default PageTransition;
