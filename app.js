const sub_butt = document.querySelector(".sub-butt")
const uid =document.querySelector(".uid")
const tit = document.querySelector(".title")
const tabl=document.querySelector(".tabl-data")
const whole_table = document.querySelector(".table")
const dropdown = document.querySelector(".custom-select")
const loader = document.querySelector(".loader")


// let url = window.location.href;
// let lp_userId=url.searchParams.get("userId");

sub_butt.addEventListener("click", fetch_data);

tit.addEventListener("click", function() {
    if(dropdown.value == "Choose Parameter...") {
        tit.disabled = true
    }
});

dropdown.addEventListener("click", function() {
    if(dropdown.value == "Choose Parameter...") {
        tit.disabled = true
    } else {
        tit.disabled = false
        if(dropdown.value=="title") {
            tit.placeholder = "Enter Title"
        } else if(dropdown.value=="genre") {
            tit.placeholder = "Enter Genre"
            
        } else if(dropdown.value=="cast") {
            tit.placeholder = "Enter Cast"
        } else if(dropdown.value=="director") {
            tit.placeholder = "Enter Director"
        }
        
    }
});

tit.addEventListener("keyup", function(event) {
    if (event.keyCode === 13) {
     event.preventDefault();
     sub_butt.click();
    }
});

whole_table.style.visibility = "hidden";
loader.style.visibility = "hidden";

function seperate(item){
    let sep = ""
    let i;
    for(i= 0; i< item.length-1; i++){
        sep+= `${item[i]}, `;
    }
    sep+= item[i]
    return sep;
}

function fetch_data(){
    tabl.innerHTML=""
    whole_table.style.visibility = "visible";
    loader.style.visibility = "visible";

    let lp_userId = window.location.search.substr(1).split("&")[0].split("=")[1];

    // let userId = uid.value;
    let userId = lp_userId;
    
    let title = tit.value
    let type = dropdown.value

    // if (!userId || !title) {
    //     whole_table.style.visibility = "hidden";
    //     alert("Please Enter Valid Data...");
    //     return
    // }
    if (!title) {
        whole_table.style.visibility = "hidden";
        alert("Please Enter Valid Data...");
        return
    }

    try{
        // fetch(`http://127.0.0.1:5000/data?u=${userId}&t=${title}`).then(response => response.json()).then(data => render_result(JSON.parse(data)));

        fetch(`http://127.0.0.1:5000/data?u=${userId}&a=${title}&t=${type}`).then(response => response.json()).then(data => render_result(JSON.parse(data)));
    } catch {
        whole_table.style.visibility = "hidden";
        loader.style.visibility = "hidden"
        alert("Please Enter Valid Data...");
    }
}

async function render_result(data) {
    if(data.length!=0){
        if(data[0].status==501) {
            loader.style.visibility = "hidden"
            whole_table.style.visibility = "hidden";
            alert("Data not available or you have entered wrong info!!!");
            return
        } else if (data[0].status==502){
            whole_table.style.visibility = "hidden";
            loader.style.visibility = "hidden"
            alert("Some error occurred during retriving your data, please try again with different Title...");
            return
        }
    } else{
        whole_table.style.visibility = "hidden";
        loader.style.visibility = "hidden"
        alert("Data not available or you have entered wrong info!!!");
        return
    }
    whole_table.style.visibility = "visible";

    let img_urls=[]
    let count= 0
    for(let i=0;i<data.length;i++) {
        let cd = data[i]
        let id = cd.id
        try {
            const response = await fetch(`https://api.themoviedb.org/3/movie/${id}?api_key=9b2ad24ea6bb0ad20f25d18dc57c43a5`);
            const url = await response.json();
            img_urls[count]=await url.poster_path;
            count+=1;
        } catch (error) {
            console.error(error);
        }
    }

    for(let i=0;i<data.length;i++) {
        let cd = data[i]
        let title = cd.title
        let genres = cd.genres
        let cast = cd.cast
        let director = cd.director
        // let vote_count = cd.vote_count
        // let vote_average = cd.vote_average
        // let release_date = cd.release_date
        // let id = cd.id
        // let est = cd.est.toPrecision(4)

        let img_url = "http://image.tmdb.org/t/p/w200" + img_urls[i];
        
        genres = seperate(genres)
        cast = seperate(cast)

        await tabl.insertAdjacentHTML("beforeend",`<tr>
            <td>
                <img src="${img_url}" alt="${title}" style="width:100px;height:150px"></img>
            </td>
            <td style="vertical-align: middle;">${title}</td>
            <td style="vertical-align: middle;">${genres}</td>
            <td style="vertical-align: middle;">${cast}</td>
            <td style="vertical-align: middle;">${director}</td>
        </tr>`)
    };
    loader.style.visibility = "hidden";
}