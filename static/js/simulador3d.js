(() => {
    "use strict";

    const config = window.SIMULATION_CONFIG;
    const greenInput = document.querySelector("#green-time");
    const redInput = document.querySelector("#red-time");
    const waveInput = document.querySelector("#green-wave");
    const toggleButton = document.querySelector("#toggle-intersection");
    const saveButton = document.querySelector("#save-simulation");
    const statusMessage = document.querySelector("#simulation-status");
    const greenOutput = document.querySelector("#green-time-output");
    const redOutput = document.querySelector("#red-time-output");
    const afterTitle = document.querySelector("#after-scene-title");
    const signalState = document.querySelector("#signal-state");
    const signalIndicatorLight = document.querySelector("#signal-indicator-light");

    if (!config || !greenInput || !redInput || !waveInput || !toggleButton || !saveButton) {
        return;
    }

    const COLORS = {
        asphalt: 0x2c3137,
        roadLine: 0xd8dedb,
        sidewalk: 0x7f898e,
        grass: 0x28794d,
        grassLight: 0x36945b,
        building: 0x9ca8a9,
        buildingLight: 0xc3cccc,
        tree: 0x348957,
        trunk: 0x765741,
        red: 0xe94e4e,
        green: 0x2ecc71,
        carWhite: 0xf0f0eb,
        carSilver: 0xaeb9c4,
        carBlue: 0x668fe2,
        glass: 0x526d7d
    };

    const state = {
        type: config.tipo === "Rotatoria" ? "Rotatoria" : "Semaforo",
        green: Number(config.tempoVerde),
        red: Number(config.tempoVermelho),
        wave: Boolean(config.ondaVerde),
        volume: Number(config.veiculosMinuto),
        beforeWorld: null,
        afterWorld: null,
        lastHudUpdate: 0,
        disposed: false
    };

    function material(color, roughness = 0.9) {
        return new THREE.MeshStandardMaterial({ color, roughness, flatShading: true });
    }

    function box(parent, width, height, depth, color, x, y, z, options = {}) {
        const mesh = new THREE.Mesh(
            new THREE.BoxGeometry(width, height, depth),
            material(color, options.roughness ?? 0.9)
        );
        mesh.position.set(x, y, z);
        if (options.rotationY) {
            mesh.rotation.y = options.rotationY;
        }
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        parent.add(mesh);
        return mesh;
    }

    function cylinder(parent, radiusTop, radiusBottom, height, color, x, y, z, segments = 8) {
        const mesh = new THREE.Mesh(
            new THREE.CylinderGeometry(radiusTop, radiusBottom, height, segments),
            material(color)
        );
        mesh.position.set(x, y, z);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        parent.add(mesh);
        return mesh;
    }

    function addRoadMarkings(scene) {
        for (let offset = -19; offset <= 17; offset += 5) {
            box(scene, 2.3, 0.025, 0.11, COLORS.roadLine, offset + 1.15, 0.035, 0);
            box(scene, 0.11, 0.025, 2.3, COLORS.roadLine, 0, 0.035, offset + 1.15);
        }

        const zebraOffsets = [-6.5, 6.5];
        zebraOffsets.forEach((offset) => {
            for (let index = 0; index < 7; index += 1) {
                const laneOffset = -2.7 + index * 0.9;
                box(scene, 0.48, 0.04, 0.62, COLORS.roadLine, offset, 0.045, laneOffset);
                box(scene, 0.62, 0.04, 0.48, COLORS.roadLine, laneOffset, 0.045, offset);
            }
        });
    }

    function addTree(scene, x, z, scale = 1) {
        const tree = new THREE.Group();
        tree.position.set(x, 0, z);
        tree.scale.setScalar(scale);
        cylinder(tree, 0.16, 0.22, 1.05, COLORS.trunk, 0, 0.52, 0, 6);
        const crown = new THREE.Mesh(
            new THREE.IcosahedronGeometry(0.78, 0),
            material(COLORS.tree)
        );
        crown.position.set(0, 1.42, 0);
        crown.castShadow = true;
        tree.add(crown);
        const upperCrown = new THREE.Mesh(
            new THREE.IcosahedronGeometry(0.52, 0),
            material(COLORS.grassLight)
        );
        upperCrown.position.set(0.11, 1.9, -0.07);
        upperCrown.castShadow = true;
        tree.add(upperCrown);
        scene.add(tree);
    }

    function addBuildingsAndGreenery(scene) {
        const buildings = [
            [-12, -12, 4.5, 6.4, 4],
            [12, -12, 5.4, 4.5, 5.8],
            [-12, 12, 5.2, 5.5, 5.3],
            [12, 12, 4.1, 6.1, 4.5],
            [-20, -14, 3.6, 4.4, 3.4],
            [19, 15, 4.4, 3.7, 4.1]
        ];
        buildings.forEach(([x, z, width, depth, height], index) => {
            const shade = index % 2 === 0 ? COLORS.building : COLORS.buildingLight;
            box(scene, width, height, depth, shade, x, height / 2, z);
            const roof = box(scene, width + 0.22, 0.18, depth + 0.22, 0x7d898c, x, height + 0.08, z);
            roof.castShadow = true;
            for (let floor = 0; floor < Math.floor(height / 1.3); floor += 1) {
                const windowY = 1.0 + floor * 1.25;
                box(scene, 0.72, 0.62, 0.07, 0x526775, x - width * 0.24, windowY, z + depth / 2 + 0.05);
                box(scene, 0.72, 0.62, 0.07, 0x526775, x + width * 0.19, windowY, z + depth / 2 + 0.05);
            }
        });

        [-1, 1].forEach((side) => {
            box(scene, 41, 0.13, 0.72, COLORS.grass, 0, 0.09, side * 5.5);
            box(scene, 0.72, 0.13, 41, COLORS.grass, side * 5.5, 0.09, 0);
        });
        [
            [-9, -8], [-16, -8], [9, -8], [16, -8],
            [-9, 8], [-16, 8], [9, 8], [16, 8],
            [-8, -16], [8, -16], [-8, 16], [8, 16]
        ].forEach(([x, z], index) => addTree(scene, x, z, index % 3 === 0 ? 0.82 : 0.68));
    }

    function addTrafficLight(scene, x, z, axis, facing) {
        const pole = new THREE.Group();
        pole.position.set(x, 0, z);
        cylinder(pole, 0.08, 0.1, 2.25, 0x434d55, 0, 1.12, 0, 6);
        box(pole, 0.43, 0.93, 0.38, 0x20262c, 0, 2.02, 0);
        const redLight = new THREE.Mesh(
            new THREE.SphereGeometry(0.115, 8, 6),
            new THREE.MeshStandardMaterial({ color: COLORS.red, emissive: 0x501111, flatShading: true })
        );
        redLight.position.set(0, 2.25, facing * 0.205);
        pole.add(redLight);
        const yellowLight = new THREE.Mesh(
            new THREE.SphereGeometry(0.115, 8, 6),
            new THREE.MeshStandardMaterial({ color: 0x574d2c, emissive: 0x151006, flatShading: true })
        );
        yellowLight.position.set(0, 2.08, facing * 0.205);
        pole.add(yellowLight);
        const greenLight = new THREE.Mesh(
            new THREE.SphereGeometry(0.115, 8, 6),
            new THREE.MeshStandardMaterial({ color: 0x31543d, emissive: 0x09150d, flatShading: true })
        );
        greenLight.position.set(0, 1.9, facing * 0.205);
        pole.add(greenLight);
        scene.add(pole);
        return { axis, redLight, yellowLight, greenLight };
    }

    function addSemaphore(scene) {
        return [
            addTrafficLight(scene, -5.15, -5.15, "x", -1),
            addTrafficLight(scene, 5.15, 5.15, "x", 1),
            addTrafficLight(scene, 5.15, -5.15, "z", -1),
            addTrafficLight(scene, -5.15, 5.15, "z", 1)
        ];
    }

    function addRoundabout(scene) {
        const curb = new THREE.Mesh(
            new THREE.CylinderGeometry(4.45, 4.45, 0.34, 24),
            material(0x9ca69e)
        );
        curb.position.y = 0.19;
        curb.receiveShadow = true;
        scene.add(curb);
        const island = new THREE.Mesh(
            new THREE.CylinderGeometry(4.15, 4.15, 0.34, 24),
            material(COLORS.grass)
        );
        island.position.y = 0.35;
        island.receiveShadow = true;
        scene.add(island);
        const islandCap = new THREE.Mesh(
            new THREE.CylinderGeometry(3.35, 3.75, 0.26, 20),
            material(COLORS.grassLight)
        );
        islandCap.position.y = 0.62;
        scene.add(islandCap);

        const outerLine = new THREE.Mesh(
            new THREE.TorusGeometry(5.15, 0.075, 5, 48),
            material(COLORS.roadLine)
        );
        outerLine.rotation.x = Math.PI / 2;
        outerLine.position.y = 0.06;
        scene.add(outerLine);
        const innerLine = new THREE.Mesh(
            new THREE.TorusGeometry(4.55, 0.075, 5, 48),
            material(COLORS.roadLine)
        );
        innerLine.rotation.x = Math.PI / 2;
        innerLine.position.y = 0.07;
        scene.add(innerLine);
        addTree(scene, -0.55, 0.15, 0.9);
        addTree(scene, 0.7, -0.5, 0.72);
        addTree(scene, 0.55, 0.85, 0.62);
    }

    function makeCar(color, axis, direction, lane, progress) {
        const group = new THREE.Group();
        const body = new THREE.Mesh(
            new THREE.BoxGeometry(1.58, 0.48, 0.87),
            material(color, 0.5)
        );
        body.position.y = 0.43;
        body.castShadow = true;
        group.add(body);

        const cabin = new THREE.Mesh(
            new THREE.BoxGeometry(0.84, 0.43, 0.68),
            material(COLORS.glass, 0.35)
        );
        cabin.position.set(-0.09, 0.85, 0);
        cabin.castShadow = true;
        group.add(cabin);

        const hood = new THREE.Mesh(
            new THREE.BoxGeometry(0.3, 0.19, 0.73),
            material(color, 0.55)
        );
        hood.position.set(0.62, 0.68, 0);
        group.add(hood);

        [-0.48, 0.48].forEach((x) => {
            [-0.43, 0.43].forEach((z) => {
                const wheel = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.19, 0.19, 0.12, 8),
                    material(0x1b2024, 0.95)
                );
                wheel.rotation.x = Math.PI / 2;
                wheel.position.set(x, 0.22, z);
                group.add(wheel);
            });
        });

        group.rotation.y = axis === "z" ? -direction * Math.PI / 2 : (direction < 0 ? Math.PI : 0);
        return { group, axis, direction, lane, progress, velocity: 0 };
    }

    function setLinearCarPosition(car) {
        const coordinate = -21 + car.progress;
        const travelCoordinate = car.direction > 0 ? coordinate : -coordinate;
        if (car.axis === "x") {
            car.group.position.x = travelCoordinate;
            car.group.position.z = car.lane;
        } else {
            car.group.position.x = car.lane;
            car.group.position.z = travelCoordinate;
        }
    }

    function disposeObject(object) {
        object.traverse((child) => {
            if (child.geometry) {
                child.geometry.dispose();
            }
            if (child.material) {
                const materials = Array.isArray(child.material) ? child.material : [child.material];
                materials.forEach((item) => item.dispose());
            }
        });
    }

    const SIGNAL_YELLOW_SECONDS = 3;
    const SIGNAL_CLEARANCE_SECONDS = 1;
    const SIMULATION_TIME_SCALE = 3;
    const SIGNAL_STOP_LINE = 11.6;

    function updateSemaphoreLights(world, delta) {
        if (!world.lights.length) {
            return;
        }
        world.phaseElapsed += delta * SIMULATION_TIME_SCALE;
        const crossingIsClear = (axis) => !world.cars.some(
            (car) => car.axis === axis
                && car.progress > SIGNAL_STOP_LINE + 0.3
                && car.progress < 30
        );

        if (world.phase === "east-west-green" && world.phaseElapsed >= Math.max(5, state.green)) {
            world.phase = "east-west-yellow";
            world.phaseElapsed = 0;
        } else if (world.phase === "east-west-yellow" && world.phaseElapsed >= SIGNAL_YELLOW_SECONDS) {
            world.phase = "clear-east-west";
            world.phaseElapsed = 0;
        } else if (
            world.phase === "clear-east-west"
            && world.phaseElapsed >= SIGNAL_CLEARANCE_SECONDS
            && crossingIsClear("x")
        ) {
            world.phase = "north-south-green";
            world.phaseElapsed = 0;
        } else if (world.phase === "north-south-green" && world.phaseElapsed >= Math.max(5, state.red)) {
            world.phase = "north-south-yellow";
            world.phaseElapsed = 0;
        } else if (world.phase === "north-south-yellow" && world.phaseElapsed >= SIGNAL_YELLOW_SECONDS) {
            world.phase = "clear-north-south";
            world.phaseElapsed = 0;
        } else if (
            world.phase === "clear-north-south"
            && world.phaseElapsed >= SIGNAL_CLEARANCE_SECONDS
            && crossingIsClear("z")
        ) {
            world.phase = "east-west-green";
            world.phaseElapsed = 0;
        }

        const phaseByName = {
            "east-west-green": { axis: "x", color: "green" },
            "east-west-yellow": { axis: "x", color: "yellow" },
            "north-south-green": { axis: "z", color: "green" },
            "north-south-yellow": { axis: "z", color: "yellow" }
        };
        const phase = phaseByName[world.phase] || { axis: null, color: "red" };
        world.greenAxis = phase.color === "green" ? phase.axis : null;
        world.signalPhase = phase;
        if (world === state.beforeWorld && signalState && signalIndicatorLight) {
            const descriptions = {
                "east-west-green": "Leste–Oeste aberto · Norte–Sul parado no vermelho",
                "east-west-yellow": "Amarelo Leste–Oeste · Norte–Sul aguardando",
                "clear-east-west": "Intervalo de segurança · liberando o cruzamento",
                "north-south-green": "Norte–Sul aberto · Leste–Oeste parado no vermelho",
                "north-south-yellow": "Amarelo Norte–Sul · Leste–Oeste aguardando",
                "clear-north-south": "Intervalo de segurança · liberando o cruzamento"
            };
            signalState.textContent = descriptions[world.phase];
            signalIndicatorLight.dataset.phase = world.phase;
        }

        world.lights.forEach((light) => {
            const activeColor = phase.axis === light.axis ? phase.color : "red";
            const isRed = activeColor === "red";
            const isYellow = activeColor === "yellow";
            const isGreen = activeColor === "green";
            light.redLight.material.color.setHex(isRed ? COLORS.red : 0x31543d);
            light.redLight.material.emissive.setHex(isRed ? 0x501111 : 0x09150d);
            light.yellowLight.material.color.setHex(isYellow ? 0xffc247 : 0x574d2c);
            light.yellowLight.material.emissive.setHex(isYellow ? 0x70410a : 0x151006);
            light.greenLight.material.color.setHex(isGreen ? COLORS.green : 0x31543d);
            light.greenLight.material.emissive.setHex(isGreen ? 0x0d5527 : 0x09150d);
        });
    }

    function buildRoundaboutRoute(entryAngle) {
        const radius = 6.15;
        const radial = (angle, distance) => new THREE.Vector3(
            Math.cos(angle) * distance,
            0.06,
            Math.sin(angle) * distance
        );
        const right = (angle) => new THREE.Vector3(-Math.sin(angle), 0, Math.cos(angle));
        const laneOffset = right(entryAngle).multiplyScalar(-0.92);
        const points = [
            radial(entryAngle, 23).add(laneOffset.clone()),
            radial(entryAngle, 16).add(laneOffset.clone()),
            radial(entryAngle, 10).add(laneOffset.clone()),
            radial(entryAngle, 7.75).add(laneOffset.clone()),
            radial(entryAngle, radius)
        ];

        const exitAngle = entryAngle - Math.PI;
        for (let step = 1; step <= 36; step += 1) {
            const angle = entryAngle - Math.PI * step / 36;
            points.push(radial(angle, radius));
        }
        const exitOffset = right(exitAngle).multiplyScalar(0.92);
        [7.4, 9.5, 15, 23].forEach((distance) => {
            points.push(radial(exitAngle, distance).add(exitOffset.clone()));
        });

        const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.35);
        const samples = curve.getSpacedPoints(640);
        const length = curve.getLength();
        const nearestSampleIndex = (target) => {
            let nearestIndex = 0;
            let nearestDistance = Infinity;
            samples.forEach((point, index) => {
                const distance = point.distanceToSquared(target);
                if (distance < nearestDistance) {
                    nearestDistance = distance;
                    nearestIndex = index;
                }
            });
            return nearestIndex;
        };
        const entryIndex = nearestSampleIndex(radial(entryAngle, radius));
        const ringEndIndex = nearestSampleIndex(radial(exitAngle, radius));

        return {
            entryAngle,
            exitAngle,
            length,
            entryDistance: length * entryIndex / (samples.length - 1),
            ringEndDistance: length * ringEndIndex / (samples.length - 1),
            samples
        };
    }

    function sampleRoute(route, distance) {
        const wrapped = ((distance % route.length) + route.length) % route.length;
        const position = wrapped / route.length * (route.samples.length - 1);
        const index = Math.min(Math.floor(position), route.samples.length - 2);
        const fraction = position - index;
        const point = route.samples[index].clone().lerp(route.samples[index + 1], fraction);
        const tangent = route.samples[index + 1].clone().sub(route.samples[index]).normalize();
        return { point, tangent, angle: Math.atan2(point.z, point.x) };
    }

    function setRouteCarPosition(car) {
        const sample = sampleRoute(car.route, car.progress);
        car.group.position.copy(sample.point);
        car.group.rotation.y = -Math.atan2(sample.tangent.z, sample.tangent.x);
        car.currentAngle = sample.angle;
    }

    function addTraffic(scene, mode) {
        const colors = [COLORS.carWhite, COLORS.carSilver, COLORS.carBlue, COLORS.carWhite];
        const cars = [];
        const routes = [
            { axis: "x", direction: 1, lane: 0.9, angle: Math.PI },
            { axis: "x", direction: -1, lane: -0.9, angle: 0 },
            { axis: "z", direction: 1, lane: -0.9, angle: -Math.PI / 2 },
            { axis: "z", direction: -1, lane: 0.9, angle: Math.PI / 2 }
        ];

        routes.forEach((route, routeIndex) => {
            if (mode === "Rotatoria") {
                const path = buildRoundaboutRoute(route.angle);
                for (let index = 0; index < 3; index += 1) {
                    const car = makeCar(
                        colors[(index + routeIndex) % colors.length],
                        route.axis,
                        route.direction,
                        route.lane,
                        index * 5.3
                    );
                    car.routeIndex = routeIndex;
                    car.route = path;
                    car.speedFactor = 0.86 + index * 0.05;
                    setRouteCarPosition(car);
                    scene.add(car.group);
                    cars.push(car);
                }
                return;
            }

            for (let index = 0; index < 4; index += 1) {
                const car = makeCar(
                    colors[(index + routeIndex) % colors.length],
                    route.axis,
                    route.direction,
                    route.lane,
                    [0, 3.8, 7.6, 11.4][index]
                );
                car.routeIndex = routeIndex;
                car.speedFactor = 0.88 + ((routeIndex + index) % 4) * 0.08;
                setLinearCarPosition(car);
                scene.add(car.group);
                cars.push(car);
            }
        });
        return cars;
    }

    function updateLinearTraffic(world, delta) {
        if (world.mode === "Semaforo") {
            updateSemaphoreLights(world, delta);
        }

        const lanes = new Map();
        world.cars.forEach((car) => {
            const key = `${car.axis}:${car.routeIndex}`;
            if (!lanes.has(key)) {
                lanes.set(key, []);
            }
            lanes.get(key).push(car);
        });

        lanes.forEach((cars) => {
            cars.sort((first, second) => first.progress - second.progress);
            cars.forEach((car, index) => {
                const leader = cars[(index + 1) % cars.length];
                let gap = leader.progress - car.progress;
                if (gap <= 0) {
                    gap += 42;
                }

                const safeGap = 3.2;
                let desiredSpeed = Math.min(3.2 * car.speedFactor, Math.max(0, (gap - safeGap) * 1.1));
                const isRed = world.mode === "Semaforo" && world.greenAxis !== car.axis;
                if (isRed && car.progress < SIGNAL_STOP_LINE) {
                    desiredSpeed = Math.min(
                        desiredSpeed,
                        Math.max(0, (SIGNAL_STOP_LINE - car.progress) * 1.15)
                    );
                }

                car.velocity += (desiredSpeed - car.velocity) * Math.min(1, delta * 1.8);
                const previousProgress = car.progress;
                let nextProgress = previousProgress + car.velocity * delta;
                if (isRed && previousProgress < SIGNAL_STOP_LINE && nextProgress >= SIGNAL_STOP_LINE) {
                    nextProgress = SIGNAL_STOP_LINE;
                    car.velocity = 0;
                }
                const maxProgress = previousProgress + Math.max(0, gap - safeGap);
                if (nextProgress > maxProgress) {
                    nextProgress = maxProgress;
                    car.velocity = Math.min(car.velocity, Math.max(0, (nextProgress - previousProgress) / Math.max(delta, 0.001)));
                }
                car.progress = nextProgress >= 42 ? nextProgress - 42 : nextProgress;
                setLinearCarPosition(car);
            });
        });
    }

    function isRoundaboutEntryBlocked(world, car) {
        const conflictAngle = 0.43;
        return world.cars.some((other) => {
            if (other === car) {
                return false;
            }
            if (
                other.progress < other.route.entryDistance
                || other.progress > other.route.ringEndDistance
            ) {
                return false;
            }
            const difference = Math.atan2(
                Math.sin(other.currentAngle - car.route.entryAngle),
                Math.cos(other.currentAngle - car.route.entryAngle)
            );
            return Math.abs(difference) < conflictAngle;
        });
    }

    function updateRoundaboutTraffic(world, delta) {
        const lanes = new Map();
        world.cars.forEach((car) => {
            if (!lanes.has(car.routeIndex)) {
                lanes.set(car.routeIndex, []);
            }
            lanes.get(car.routeIndex).push(car);
        });

        lanes.forEach((cars) => {
            cars.sort((first, second) => first.progress - second.progress);
            cars.forEach((car, index) => {
                const leader = cars[(index + 1) % cars.length];
                let gap = leader.progress - car.progress;
                if (gap <= 0) {
                    gap += car.route.length;
                }
                const safeGap = 3.2;
                let desiredSpeed = Math.min(3.1 * car.speedFactor, Math.max(0, (gap - safeGap) * 1.15));
                const entryStop = car.route.entryDistance - 2.7;
                if (
                    car.progress < entryStop
                    && isRoundaboutEntryBlocked(world, car)
                ) {
                    desiredSpeed = Math.min(desiredSpeed, Math.max(0, (entryStop - car.progress) * 1.1));
                }

                car.velocity += (desiredSpeed - car.velocity) * Math.min(1, delta * 1.8);
                const previousProgress = car.progress;
                let nextProgress = previousProgress + car.velocity * delta;
                if (
                    car.progress < entryStop
                    && isRoundaboutEntryBlocked(world, car)
                    && nextProgress >= entryStop
                ) {
                    nextProgress = entryStop;
                    car.velocity = 0;
                }
                const maxProgress = previousProgress + Math.max(0, gap - safeGap);
                if (nextProgress > maxProgress) {
                    nextProgress = maxProgress;
                    car.velocity = Math.min(car.velocity, Math.max(0, (nextProgress - previousProgress) / Math.max(delta, 0.001)));
                }
                car.progress = nextProgress >= car.route.length
                    ? nextProgress - car.route.length
                    : nextProgress;
                setRouteCarPosition(car);
            });
        });
    }

    function makeWorld(container, mode) {
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x20272e);
        scene.fog = new THREE.Fog(0x20272e, 45, 82);

        const width = Math.max(container.clientWidth, 1);
        const height = Math.max(container.clientHeight, 1);
        const aspect = width / height;
        const frustum = 26;
        const camera = new THREE.OrthographicCamera(
            -frustum * aspect / 2,
            frustum * aspect / 2,
            frustum / 2,
            -frustum / 2,
            0.1,
            150
        );
        camera.position.set(28, 37, 30);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
        renderer.setSize(width, height);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.outputEncoding = THREE.sRGBEncoding;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.12;
        container.replaceChildren(renderer.domElement);

        scene.add(new THREE.HemisphereLight(0xdce9ed, 0x3c453e, 2.05));
        const sunlight = new THREE.DirectionalLight(0xffe6bd, 2.1);
        sunlight.position.set(-14, 28, 13);
        sunlight.castShadow = true;
        sunlight.shadow.mapSize.set(1024, 1024);
        sunlight.shadow.camera.left = -30;
        sunlight.shadow.camera.right = 30;
        sunlight.shadow.camera.top = 30;
        sunlight.shadow.camera.bottom = -30;
        scene.add(sunlight);

        const ground = new THREE.Mesh(
            new THREE.PlaneGeometry(78, 78),
            material(0x353d40)
        );
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.16;
        ground.receiveShadow = true;
        scene.add(ground);

        box(scene, 46, 0.12, 8.6, COLORS.asphalt, 0, 0, 0);
        box(scene, 8.6, 0.12, 46, COLORS.asphalt, 0, 0, 0);
        box(scene, 46, 0.08, 1.15, COLORS.sidewalk, 0, -0.025, 4.92);
        box(scene, 46, 0.08, 1.15, COLORS.sidewalk, 0, -0.025, -4.92);
        box(scene, 1.15, 0.08, 46, COLORS.sidewalk, 4.92, -0.025, 0);
        box(scene, 1.15, 0.08, 46, COLORS.sidewalk, -4.92, -0.025, 0);
        addRoadMarkings(scene);
        addBuildingsAndGreenery(scene);

        const lights = mode === "Semaforo" ? addSemaphore(scene) : [];
        if (mode === "Rotatoria") {
            addRoundabout(scene);
        }
        const cars = addTraffic(scene, mode);
        if (mode === "Rotatoria") {
            cars.forEach((car, index) => {
                car.angle = (Math.PI * 2 * index) / cars.length;
            });
        }

        const world = {
            scene,
            camera,
            renderer,
            lights,
            cars,
            mode,
            greenAxis: "x",
            phase: "east-west-green",
            phaseElapsed: 0,
            signalPhase: { axis: "x", color: "green" },
            resizeObserver: null
        };
        world.resizeObserver = new ResizeObserver(() => {
            if (state.disposed || !container.isConnected) {
                return;
            }
            const nextWidth = Math.max(container.clientWidth, 1);
            const nextHeight = Math.max(container.clientHeight, 1);
            const nextAspect = nextWidth / nextHeight;
            world.camera.left = -frustum * nextAspect / 2;
            world.camera.right = frustum * nextAspect / 2;
            world.camera.top = frustum / 2;
            world.camera.bottom = -frustum / 2;
            world.camera.updateProjectionMatrix();
            world.renderer.setSize(nextWidth, nextHeight);
        });
        world.resizeObserver.observe(container);
        return world;
    }

    function replaceWorld(world, container, mode) {
        if (world) {
            world.resizeObserver.disconnect();
            world.renderer.dispose();
            disposeObject(world.scene);
        }
        return makeWorld(container, mode);
    }

    function metricsForCurrentScenario() {
        const volume = Math.max(0, Number(state.volume) || 0);
        if (state.type === "Rotatoria") {
            const wait = Math.max(3, 4 + volume * 0.2);
            const capacity = 34;
            return { wait, congestion: congestionFor(volume / capacity), volume };
        }

        const green = Math.max(1, state.green);
        const red = Math.max(1, state.red);
        let wait = red / 2 + volume * 0.2;
        if (state.wave) {
            wait *= 0.76;
        }
        const capacity = Math.max(1, (green / (green + red)) * 42);
        return { wait, congestion: congestionFor(volume / capacity), volume };
    }

    function congestionFor(ratio) {
        if (ratio < 0.72) {
            return "BAIXO";
        }
        if (ratio < 1.18) {
            return "MEDIO";
        }
        return "ALTO";
    }

    function updateHud() {
        const metrics = metricsForCurrentScenario();
        document.querySelector("#hud-wait").textContent = metrics.wait.toFixed(1);
        document.querySelector("#hud-vehicles").textContent = String(metrics.volume);
        const congestion = document.querySelector("#hud-congestion");
        congestion.textContent = metrics.congestion;
        congestion.className = `badge badge-${metrics.congestion.toLowerCase()}`;
    }

    function updateControlLabels() {
        greenOutput.textContent = greenInput.value;
        redOutput.textContent = redInput.value;
        state.green = Number(greenInput.value);
        state.red = Number(redInput.value);
        state.wave = waveInput.checked;
        statusMessage.textContent = "Indicadores atualizados como estimativas educativas; não representam medição de campo.";
        updateHud();
    }

    function updateIntersectionMode() {
        const roundabout = state.type === "Rotatoria";
        toggleButton.setAttribute("aria-pressed", String(roundabout));
        toggleButton.textContent = roundabout ? "Trocar para semáforo" : "Trocar para rotatória";
        afterTitle.textContent = roundabout ? "Rotatória proposta" : "Cenário ajustado";
        statusMessage.textContent = "Cenário atualizado. Indicadores são estimativas educativas, não medições de campo.";
        if (window.THREE && window.WebGLRenderingContext) {
            try {
                state.afterWorld = replaceWorld(
                    state.afterWorld,
                    document.querySelector("#scene-after"),
                    state.type
                );
            } catch (error) {
                addFallbackMessage(document.querySelector("#scene-after"), error);
                state.afterWorld = null;
            }
        }
        updateHud();
    }

    async function saveResults() {
        saveButton.disabled = true;
        statusMessage.textContent = "Salvando resultados da simulação...";
        const metrics = metricsForCurrentScenario();
        try {
            const response = await fetch(config.salvarUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": config.csrfToken
                },
                body: JSON.stringify({
                    tipo_intersecao: state.type,
                    tempo_verde: state.green,
                    tempo_vermelho: state.red,
                    onda_verde: state.wave,
                    tempo_espera_medio: Number(metrics.wait.toFixed(1)),
                    congestionamento: metrics.congestion,
                    veiculos_minuto: metrics.volume
                })
            });
            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.error || "Não foi possível salvar a simulação.");
            }
            statusMessage.textContent = payload.message;
        } catch (error) {
            statusMessage.textContent = error.message || "Não foi possível salvar a simulação. Tente novamente.";
        } finally {
            saveButton.disabled = false;
        }
    }

    function addFallbackMessage(container, error) {
        console.error("Não foi possível inicializar a visualização 3D.", error);
        container.innerHTML = "";
        const message = document.createElement("div");
        message.className = "scene-canvas-fallback";
        message.textContent = "A visualização 3D não pôde ser iniciada neste navegador. Confira o suporte a WebGL e recarregue a página.";
        container.append(message);
    }

    function initialize() {
        if (!window.THREE || !window.WebGLRenderingContext) {
            document.querySelectorAll(".scene-canvas").forEach((container) => {
                addFallbackMessage(container, new Error("Three.js ou WebGL não está disponível."));
            });
            saveButton.addEventListener("click", saveResults);
            greenInput.addEventListener("input", updateControlLabels);
            redInput.addEventListener("input", updateControlLabels);
            waveInput.addEventListener("change", updateControlLabels);
            toggleButton.addEventListener("click", () => {
                state.type = state.type === "Rotatoria" ? "Semaforo" : "Rotatoria";
                updateIntersectionMode();
            });
            updateControlLabels();
            return;
        }

        try {
            state.beforeWorld = makeWorld(document.querySelector("#scene-before"), "Semaforo");
            state.afterWorld = makeWorld(document.querySelector("#scene-after"), state.type);
        } catch (error) {
            document.querySelectorAll(".scene-canvas").forEach((container) => addFallbackMessage(container, error));
        }

        greenInput.addEventListener("input", updateControlLabels);
        redInput.addEventListener("input", updateControlLabels);
        waveInput.addEventListener("change", updateControlLabels);
        toggleButton.addEventListener("click", () => {
            state.type = state.type === "Rotatoria" ? "Semaforo" : "Rotatoria";
            updateIntersectionMode();
        });
        saveButton.addEventListener("click", saveResults);
        updateControlLabels();

        const animate = (now) => {
            if (state.disposed) {
                return;
            }
            const delta = Math.min(0.05, Math.max(0, (now - (state.previousFrame || now)) / 1000));
            state.previousFrame = now;
            [state.beforeWorld, state.afterWorld].forEach((world) => {
                if (!world) {
                    return;
                }
                if (world.mode === "Rotatoria") {
                    updateRoundaboutTraffic(world, delta);
                } else {
                    updateLinearTraffic(world, delta);
                }
                world.renderer.render(world.scene, world.camera);
            });
            if (now - state.lastHudUpdate > 500) {
                updateHud();
                state.lastHudUpdate = now;
            }
            window.requestAnimationFrame(animate);
        };
        window.requestAnimationFrame(animate);
        window.addEventListener("pagehide", () => {
            state.disposed = true;
            [state.beforeWorld, state.afterWorld].forEach((world) => {
                if (world) {
                    world.resizeObserver.disconnect();
                    world.renderer.dispose();
                    disposeObject(world.scene);
                }
            });
        }, { once: true });
    }

    if (window.THREE) {
        initialize();
    } else {
        window.addEventListener("load", initialize, { once: true });
    }
})();
