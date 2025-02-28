document.addEventListener('DOMContentLoaded'){
    document.queyrySelectorAll('.star-rating').forEach(function (rating){
        const stars = rating.querySeectorAll('label');
        stars.forEach(function (star){
            star.addEventListener('click' , function (){
                const value = this.previousElementSibling.value;
                console.log('Selected rating: ${value}');
            })
        })
    })
}
