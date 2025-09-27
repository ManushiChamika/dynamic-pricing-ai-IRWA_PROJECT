const CompanyLogo = () => {
  const logos = [
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742268610/Image%20Files/Marquee/tajpgulnccaywqi57mct.png", alt: "Discord", width: 600, height: 120, },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742268631/Image%20Files/Marquee/jllsywngxyklkxyxnesw.png", alt: "NCR", width: 600, height: 120 },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742268667/Image%20Files/Marquee/rtqt0eazegblisvwdcqy.png", alt: "Monda.com", width: 600, height: 120 },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742268687/Image%20Files/Marquee/zfu2p9gdqrxteqelxkhy.png", alt: "Ted", width: 600, height: 120 },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742268706/Image%20Files/Marquee/smgruuhsqewckwcovebb.png", alt: "Dropbox", width: 600, height: 120 },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742268729/Image%20Files/Marquee/tpmxw56zpyxz3wgiy1d2.png", alt: "", width: 600, height: 120 },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742269284/Image%20Files/Marquee/t8cljyhmtsnkbn3kjmo3.png", alt: "G", width: 600, height: 120 },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742269342/Image%20Files/Marquee/kic1f4n17b27ydmpeaim.png", alt: "H", width: 600, height: 120 },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742269370/Image%20Files/Marquee/w2qa2osuhdvgcsmyl2v7.png", alt: "I", width: 600, height: 120 },
    { src: "https://res.cloudinary.com/dovdejenw/image/upload/v1742269391/Image%20Files/Marquee/qvyrfrmtfpq8mtylyn1w.png", alt: "J", width: 600, height: 120 },
  ];

  return (
    <div className="relative bg-gradient-to-r from-red-900 via-gray-900 to-blue-700 overflow-hidden py-8">
      {/* Marquee animation container */}
      <div
        style={{
          display: 'flex',
          animation: 'marquee 60s linear infinite',  // Slower speed for smoother scrolling
          whiteSpace: 'nowrap',  // Prevent wrapping for smooth scrolling
        }}
      >
        {/* Duplicate the logos array for seamless looping */}
        {[...logos, ...logos].map((logo, index) => (
          <div
            key={index}
            style={{
              flexShrink: 0,
              display: 'flex',
              justifyContent: 'center',
              paddingLeft: '16px',
              paddingRight: '16px',
            }}
          >
            <img
              src={logo.src}
              alt={logo.alt}
              width={logo.width}
              height={logo.height}
              style={{
                objectFit: 'fill',
                flexShrink: 1,
              }}
              loading="lazy"
            />
          </div>
        ))}
      </div>

      {/* Gradient overlay */}
      <div
        className="absolute inset-y-0 left-0 w-[20%]"
        style={{
          background: 'linear-gradient(to right, black, transparent)',
        }}
      ></div>
      <div
        className="absolute inset-y-0 right-0 w-[20%]"
        style={{
          background: 'linear-gradient(to left, black, transparent)',
        }}
      ></div>
    </div>
  );
};

export default CompanyLogo;
