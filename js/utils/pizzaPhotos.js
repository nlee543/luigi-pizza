// Presentation-only assets: recipe quantities, prices and backend IDs are unchanged.
export const PIZZA_PHOTOS = {
  classic: {
    src: 'assets/pizza-classic.jpg',
    alt: 'Plain cheese pizza with melted mozzarella and tomato sauce on a metal tray',
    width: 1000,
    height: 917,
  },
  pepperoni: {
    src: 'assets/pizza-pepperoni.jpg',
    alt: 'Cheese and pepperoni pizza on a wooden serving board',
    width: 1000,
    height: 944,
  },
  garden: {
    src: 'assets/pizza-garden.jpg',
    alt: 'Vegetable pizza topped with sliced mushrooms, green bell peppers and onions',
    width: 800,
    height: 800,
  },
};

export function photoForToppings(toppings) {
  const key = [...toppings].sort().join(',');
  if (!key) return PIZZA_PHOTOS.classic;
  if (key === 'pepperoni') return PIZZA_PHOTOS.pepperoni;
  if (key === 'mushrooms,onions,peppers') return PIZZA_PHOTOS.garden;
  return {
    src: 'assets/pizza.jpg',
    alt: 'Illustrative photograph of a cheese pizza with basil; your custom toppings are listed below',
    width: 1000,
    height: 667,
  };
}
