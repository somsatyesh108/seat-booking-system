// TitleRow.jsx - A heading, a "See all" link, and a row of title cards that scrolls sideways.

import { useRef } from "react";
import { Link } from "react-router-dom";
import TitleCard from "./TitleCard";

export default function TitleRow({ heading, seeAllTo, items }) {
  const scroller = useRef(null);

  if (items.length === 0) return null;

  function scrollBy(direction) {
    const element = scroller.current;
    if (element) {
      element.scrollBy({ left: direction * element.clientWidth * 0.8, behavior: "smooth" });
    }
  }

  return (
    <section className="row">
      <div className="row-head">
        <h2>{heading}</h2>
        {seeAllTo && <Link to={seeAllTo}>See all</Link>}
        <div className="row-arrows">
          <button aria-label={`Scroll ${heading} left`} onClick={() => scrollBy(-1)}>‹</button>
          <button aria-label={`Scroll ${heading} right`} onClick={() => scrollBy(1)}>›</button>
        </div>
      </div>
      <div className="row-scroller" ref={scroller}>
        {items.map((item) => (
          <TitleCard key={item.slug} item={item} />
        ))}
      </div>
    </section>
  );
}