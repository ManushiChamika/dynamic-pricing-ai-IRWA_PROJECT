import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Slider from 'react-slick';
import ProductCards from './ProductCards';
import 'slick-carousel/slick/slick.css';
import 'slick-carousel/slick/slick-theme.css';

const OfferedProducts = () => {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch products from the database when the component mounts.
  useEffect(() => {
    const fetchProducts = async () => {
      setIsLoading(true);
      try {
        const response = await axios.get("http://localhost:5000/api/products");
        if (response.status === 200) {
          setProducts(response.data);
        }
      } catch (error) {
        console.error("Error fetching products:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, []);

  // Filter products that have a discounted price lower than the original price
  const specialOfferProducts = products.filter(
    (product) => product.discountPrice && product.discountPrice < product.price
  );

  // Slick Carousel settings
  const settings = {
    dots: true,
    infinite: true,
    speed: 500,
    slidesToShow: specialOfferProducts.length < 4 ? specialOfferProducts.length : 4,
    slidesToScroll: 1,
    autoplay: true,
    autoplaySpeed: 3000,
    arrows: true,
    centerMode: false,
    responsive: [
      {
        breakpoint: 1024,
        settings: {
          slidesToShow: 3,
        },
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 2,
        },
      },
      {
        breakpoint: 480,
        settings: {
          slidesToShow: 1,
        },
      },
    ],
  };

  return (
    <div className='bg-black pb-3'>
      <section className='section__container product__container'>
        <h2 className='section__header'>Special Offers</h2>
        <p className='section__subheader mb-12'>
          Get the best deals on high-performance laptops, gaming accessories, and essential tech upgrades—only at Alpha IT Solutions!
        </p>

        {isLoading ? (
          <p>Loading products...</p>
        ) : specialOfferProducts.length > 0 ? (
          <Slider {...settings} className="slider-container">
            {specialOfferProducts.map((product, index) => (
              <div key={index} className="px-2">
                <ProductCards products={[product]} />
              </div>
            ))}
          </Slider>
        ) : (
          <p>No special offers available at the moment.</p>
        )}
      </section>
    </div>
  );
};

export default OfferedProducts;
